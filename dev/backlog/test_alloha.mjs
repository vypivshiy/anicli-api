/**
 * Extract direct HLS stream URLs from Alloha player.
 *
 * Usage:
 *   node test_alloha.mjs [PLAYER_URL] [--full] [--json]
 *
 * --full  – print full URLs
 * --json  – output JSON to stdout (all other output goes to stderr)
 */

import puppeteer from "puppeteer";

const args = process.argv.slice(2);
const PRINT_FULL = args.includes("--full");
const JSON_OUTPUT = args.includes("--json");
const PLAYER_URL =
  args.find((a) => !a.startsWith("--")) ||
  "https://alloha.yani.tv/?token_movie=d9a17e70501e90d29994419cd7575e&season=1&episode=4&token=8b5512267a2a52e9de06d67d342e0c&skip_button=%5Bopening%5D0-39%2C%5Bending%5D1369-1388";

// In --json mode, all logs go to stderr so stdout is clean JSON
function log(...msg) {
  if (JSON_OUTPUT) {
    console.error(...msg);
  } else {
    console.log(...msg);
  }
}

function parseStreamResponse(data) {
  const results = [];
  for (const source of data.hlsSource || []) {
    const qualities = {};
    for (const [q, rawUrl] of Object.entries(source.quality || {})) {
      qualities[q] = rawUrl.split(" or ")[0].replace(/\\\//g, "/");
    }
    results.push({
      label: source.label,
      audioId: source.audioId,
      default: source.default || false,
      qualities,
    });
  }
  return results;
}

async function main() {
  log("URL:", PLAYER_URL);
  log("Fetching player HTML...");

  const res = await fetch(PLAYER_URL, {
    headers: {
      "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:149.0) Gecko/20100101 Firefox/149.0",
      Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
      "Accept-Language": "en-US,en;q=0.9",
      "Accept-Encoding": "gzip, deflate, br, zstd",
      Referer: "https://old.yummyani.me/",
      "Upgrade-Insecure-Requests": "1",
      "Sec-Fetch-Dest": "iframe",
      "Sec-Fetch-Mode": "navigate",
      "Sec-Fetch-Site": "cross-site",
      "Sec-Fetch-Storage-Access": "none",
      "Sec-GPC": "1",
      Priority: "u=4",
    },
  });

  log("HTML fetch status:", res.status, res.statusText);

  if (!res.ok) {
    console.error(`Failed to fetch player page: HTTP ${res.status}`);
    process.exit(1);
  }

  let html = await res.text();
  log("HTML length:", html.length);

  // Debug: check if HTML contains expected data
  const hasUserParam = html.includes("userParam");
  const hasFileList = html.includes("fileList");
  const hasViewporti = html.includes("viewporti");
  const hasMovie = html.includes("const movie");
  log("HTML contains: userParam=" + hasUserParam + " fileList=" + hasFileList + " viewporti=" + hasViewporti + " movie=" + hasMovie);

  if (!hasFileList) {
    log("WARNING: fileList not found in HTML. Page might be invalid.");
    log("HTML preview:", html.substring(0, 500));
  }

  // Patch out the iframe guard and SRI checks
  html = html.replace(
    /<script>var isFramed[\s\S]*?<\/script>/,
    "<script>var isFramed=true;</script>"
  );
  html = html.replace(/ integrity="[^"]*"/g, "");

  log("Launching headless browser...");
  const browser = await puppeteer.launch({
    headless: true,
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  });

  const page = await browser.newPage();
  await page.setUserAgent(
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:149.0) Gecko/20100101 Firefox/149.0"
  );
  await page.setExtraHTTPHeaders({
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-GPC": "1",
  });

  // Collect all requests/responses for debugging
  let apiResponseData = null;
  let apiResponseStatus = null;
  let borthHeader = null;
  let m3u8Headers = null;
  const allRequests = [];
  const allResponses = [];

  page.on("response", async (response) => {
    const url = response.url();
    allResponses.push({ url: url.substring(0, 120), status: response.status() });

    if (url.includes("/bnsi/")) {
      log("API response:", response.status(), url.substring(0, 120));
      apiResponseStatus = response.status();
      try {
        apiResponseData = await response.json();
        log("API response data keys:", Object.keys(apiResponseData));
      } catch (e) {
        log("API response parse error:", e.message);
        apiResponseData = null;
      }
    }
  });

  page.on("request", (request) => {
    const url = request.url();
    if (url.includes("/bnsi/")) {
      log("API request:", request.method(), url.substring(0, 120));
      borthHeader = request.headers()["borth"] || null;
      log("Borth header:", borthHeader ? borthHeader.substring(0, 40) + "..." : "null");
      log("POST body:", request.postData());
    }
    // Capture m3u8 request headers from browser
    if (url.includes("stream-balancer") && url.includes("master.m3u8")) {
      m3u8Headers = request.headers();
      log("m3u8 request headers:", JSON.stringify(m3u8Headers, null, 2));
    }
    // Log JS file loads
    if (url.includes("/build/") && url.endsWith(".js")) {
      allRequests.push(url.substring(0, 120));
    }
  });

  page.on("console", (msg) => {
    log("[browser]", msg.text());
  });

  page.on("pageerror", (err) => {
    log("[browser error]", err.message);
  });

  try {
    await page.setRequestInterception(true);
    page.on("request", (request) => {
      if (request.url().startsWith("https://alloha.yani.tv/?") && request.isNavigationRequest()) {
        log("Serving patched HTML for navigation request");
        request.respond({ status: 200, contentType: "text/html; charset=utf-8", body: html });
      } else {
        request.continue();
      }
    });

    log("Loading player in browser...");
    await page.goto(PLAYER_URL, { waitUntil: "networkidle2", timeout: 30000 });
    log("Page loaded. Waiting 5s for JS execution...");
    await new Promise((r) => setTimeout(r, 5000));

    log("JS files loaded:", allRequests.length);
    log("All responses:", JSON.stringify(allResponses, null, 2));

    if (borthHeader) {
      log("\nBorth:", borthHeader);
      const [, b64] = borthHeader.split("|");
      if (b64) {
        const decoded = Buffer.from(b64, "base64").toString();
        log("Decoded:", decoded);
      }
    }

    if (!apiResponseData) {
      console.error("No API response intercepted. Dumping all responses:");
      console.error(JSON.stringify(allResponses, null, 2));
      process.exit(1);
    }

    log("API status:", apiResponseStatus);

    if (apiResponseStatus !== 200) {
      console.error("API returned non-200 status:", apiResponseStatus);
      console.error("Response:", JSON.stringify(apiResponseData).substring(0, 500));
      process.exit(1);
    }

    const streams = parseStreamResponse(apiResponseData);
    const borthHash = borthHeader ? borthHeader.split("|")[0] : null;
    const pnk = apiResponseData.pnk || null;

    // Build headers from what the browser actually sends for m3u8
    // Fall back to constructed headers if m3u8 wasn't captured
    let streamHeaders;
    if (m3u8Headers) {
      log("Using captured m3u8 browser headers");
      streamHeaders = {};
      for (const [k, v] of Object.entries(m3u8Headers)) {
        streamHeaders[k] = v;
      }
    } else {
      log("WARNING: m3u8 request not captured, constructing headers");
      streamHeaders = {};
      if (borthHash) streamHeaders["Accepts-Controls"] = borthHash;
      if (pnk) streamHeaders["Authorizations"] = "Bearer " + pnk;
      streamHeaders["Origin"] = "https://alloha.yani.tv";
      streamHeaders["Referer"] = "https://alloha.yani.tv/";
    }

    log("Parsed", streams.length, "stream sources");
    log("Stream headers:", JSON.stringify(streamHeaders, null, 2));

    if (JSON_OUTPUT) {
      // ONLY this goes to stdout
      process.stdout.write(JSON.stringify({ streams, headers: streamHeaders }));
    } else {
      console.log("\n=== m3u8 Request Headers (from browser) ===");
      for (const [k, v] of Object.entries(streamHeaders)) {
        console.log(`  ${k}: ${v.length > 80 ? v.substring(0, 77) + "..." : v}`);
      }
      console.log("\n=== Stream Sources ===\n");
      for (const stream of streams) {
        const tag = stream.default ? " [DEFAULT]" : "";
        console.log(`${stream.label}${tag}  (audioId=${stream.audioId})`);
        for (const [q, url] of Object.entries(stream.qualities)) {
          console.log(`  ${q}p: ${PRINT_FULL ? url : url.substring(0, 90) + "..."}`);
        }
        console.log();
      }

      const defaultStream = streams.find((s) => s.default);
      if (defaultStream) {
        const best = Object.entries(defaultStream.qualities).sort(
          (a, b) => parseInt(b[0]) - parseInt(a[0])
        )[0];
        if (best) {
          // Test: try fetching the m3u8 URL with the same headers
          log("\nTesting m3u8 URL access via Node.js fetch...");
          try {
            const testHeaders = { ...streamHeaders };
            testHeaders["user-agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:149.0) Gecko/20100101 Firefox/149.0";
            const testRes = await fetch(best[1], { headers: testHeaders });
            log("Test fetch status:", testRes.status, testRes.statusText);
            if (testRes.ok) {
              const body = await testRes.text();
              log("m3u8 body preview:", body.substring(0, 200));
              console.log("\n=== m3u8 test: OK (status " + testRes.status + ") ===");
            } else {
              const body = await testRes.text();
              log("Error response:", body.substring(0, 300));
              console.log("\n=== m3u8 test: FAILED (status " + testRes.status + ") ===");
              // Try with minimal headers
              log("\nRetrying with minimal auth headers only...");
              const minHeaders = {};
              if (borthHash) minHeaders["Accepts-Controls"] = borthHash;
              if (apiResponseData.pnk) minHeaders["Authorizations"] = "Bearer " + apiResponseData.pnk;
              minHeaders["Origin"] = "https://alloha.yani.tv";
              minHeaders["Referer"] = "https://alloha.yani.tv/";
              minHeaders["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:149.0) Gecko/20100101 Firefox/149.0";
              const minRes = await fetch(best[1], { headers: minHeaders });
              log("Minimal headers test status:", minRes.status, minRes.statusText);
              if (minRes.ok) {
                const minBody = await minRes.text();
                log("m3u8 body preview:", minBody.substring(0, 200));
              } else {
                log("Error:", (await minRes.text()).substring(0, 300));
              }
            }
          } catch (e) {
            log("Test fetch error:", e.message);
            console.log("\n=== m3u8 test: ERROR ===");
          }
          const UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:149.0) Gecko/20100101 Firefox/149.0";
          console.log(`=== Best quality: ${best[0]}p ===`);
          console.log(best[1]);
          console.log("\n=== mpv command ===");
          const headerArgs = Object.entries(streamHeaders)
            .map(([k, v]) => `"${k}: ${v}"`)
            .join(",");
          console.log(`mpv --user-agent="${UA}" --http-header-fields=${headerArgs} "${best[1]}"`);
          console.log("\n=== curl command ===");
          let curl = `curl "${best[1]}"`;
          curl += ` \\\n  -H 'User-Agent: ${UA}'`;
          for (const [k, v] of Object.entries(streamHeaders)) {
            curl += ` \\\n  -H '${k}: ${v}'`;
          }
          console.log(curl);
        }
      }
    }
  } finally {
    await browser.close();
  }
}

main().catch((e) => {
  console.error("Error:", e.message || e);
  process.exit(1);
});
