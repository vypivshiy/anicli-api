# Alloha Player Reverse Engineering Notes

## Overview

Alloha player (`alloha.yani.tv`) serves HLS video streams. The flow to extract direct `.m3u8` URLs involves:
1. Fetching the player page HTML
2. Extracting movie metadata from embedded JSON
3. Generating a `Borth` authentication header
4. POSTing to the API endpoint
5. Parsing the obfuscated response

---

## 1. Player Page

**URL format:**
```
https://alloha.yani.tv/?token_movie={movie_token}&season={s}&episode={e}&token={session_token}
```

**Required headers:** `Referer: https://old.yummyani.me/`

**Key data extracted from HTML:**

### `userParam` (inline JS)
```js
const userParam = {
  token: '8b5512267a2a52e9de06d67d342e0c',  // session token, used in API POST body
  domain: 'https%3A%2F%2Fold.yummyani.me%2F',
  device: 0,
  selector: 2,
  autoplay: 0,
  audio: '',
  subtitle: '',
  // ...
};
```

### `movie` (inline JS)
```js
const movie = {
  id: 'd9a17e70501e90d29994419cd7575e',  // movie token (NOT the numeric ID)
  type: 'movie',
};
```

### `fileList` (inline JS, JSON.parse)
Contains the **numeric movie ID** needed for the API endpoint:
```js
const fileList = JSON.parse('{"type":"serial","active":{"id":1227156, ...}, ...}');
```
- `fileList.active.id` = `1227156` — this is the numeric movie ID used in the API URL path
- Each translation has its own `id` field
- `fileList.active.id_translation` — translation identifier (66=dub Russian, 154=Ukrainian, 79=subs, etc.)

### `viewporti` meta tag
```html
<meta name="viewporti" content="4F1M5NJ23MwuRcJp4TZsxRPZkkWHFGD0FWkRxFYxlwJANddm80wmtj3ONUaOW1WWVTjzX1n2ZYSdOaWeNNMTRMQM">
```
Base64-encoded binary data (94 bytes). Likely part of the Borth header generation — character set matches the third field of the decoded Borth data.

---

## 2. Anti-Iframe Guard

The page has a synchronous script that destroys content if NOT loaded inside an iframe:
```js
var isFramed=false;
try{isFramed=window!=window.top||document!=top.document||self.location!=top.location}
catch(e){isFramed=true}
if(!isFramed){ /* removes body content */ }
```
**Bypass:** Replace with `var isFramed=true;` before loading in headless browser.

Also, scripts have **SRI (Subresource Integrity)** attributes that block loading in cross-origin contexts:
```html
<script src="/build/app.7c861a4f.js" defer integrity="sha384-...">
```
**Bypass:** Remove `integrity="..."` attributes from the HTML.

---

## 3. API Endpoint

```
POST https://alloha.yani.tv/bnsi/movies/{movie_id}
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
Borth: {hash}|{base64_data}
X-Requested-With: XMLHttpRequest
Origin: https://alloha.yani.tv
Referer: https://alloha.yani.tv/?token_movie=...&...

Body: token={session_token}&av1=true&autoplay=0&audio=&subtitle=
```

Where `{movie_id}` = `fileList.active.id` (e.g. `1227156`).

---

## 4. Borth Header Structure

Format: `{sha256_hex}|{base64_encoded}`

### Decoded base64 part
```
bLhentLPLeA|1776648143|NdWSy25XkAPvsIttmwTzV41Dtj3CBaqrfBLZig6dO2s
```
Three pipe-separated fields:
1. **First field** (11 chars): `bLhentLPLeA` — looks like a base64-encoded short value (possibly derived from viewporti or a server token)
2. **Second field** (10 chars): `1776648143` — **Unix timestamp** in seconds
3. **Third field** (~44 chars): `NdWSy25XkAPvsIttmwTzV41Dtj3CBaqrfBLZig6dO2s` — alphanumeric+hyphens+underscores token

### SHA-256 hash (first part)
64 hex chars = SHA-256 of **unknown input**. Tested and ruled out:
- NOT sha256(base64_string)
- NOT sha256(decoded_string)
- NOT sha256(token)
- NOT sha256(movie_id)
- NOT sha256(token+movie_id) or any simple concatenation
- NOT HMAC-SHA256 with any obvious key/data pair

The hash is likely computed from a combination involving the viewporti value, the timestamp, and possibly other page data.

### Observations
- The hash stays the same across multiple requests with the same page load (`d5a6c8ea...` in user's curl, `b2c198d2...` in headless browser test)
- The timestamp changes with each request
- The third field changes with each request
- The **viewporti** content has a similar character set to the third Borth field (base64url alphabet)

---

## 5. JS Source Analysis

### Files
- `runtime.b0bc62c7.js` — webpack runtime
- `539.51777e24.js` — vendor bundle (jQuery, HLS.js, etc.)
- `app.7c861a4f.js` — main application (~526KB, heavily obfuscated)

### Obfuscation
The app.js uses a **string array rotation** pattern:
- A large array of string literals at the top
- `mC(index1, index2)` function decodes strings via offset lookup
- Variable names are obfuscated (`yI`, `yG`, `yP`, `yO`, `yh`, `Xp`, etc.)

### Borth Generation (found at offset ~465270 in app.js)
```js
// Pseudocode (de-obfuscated):
const urlPath = (fileList.type === 'movie') ? '/serials/' : '/movies/';
fetch('/bnsi' + urlPath + movieId, {
  method: 'POST',
  data: postData,
  headers: {
    'Borth': '' + yI + '|' + yG(Xp, yh)
  }
})
```

### Variable trace
- `yI` = result of a prior async call (`JT()`) — likely a server-provided hash/token
- `Xp = yP(yO(yF, yh), yh)` — computed from `yF` (extracted from an earlier response) and `yh`
- `yG(Xp, yh)` — encodes `Xp` and `yh` into the base64 part
- `sha256` is referenced in the string array, used elsewhere in the code as `Jx['sha256']`

The generation involves **multiple sequential async operations** — the Borth header cannot be computed from static page data alone. There appears to be a prior API call that provides intermediate tokens.

---

## 6. Response Format

```json
{
  "skipTime": "0-49,1294-1348",
  "hlsSource": [
    {
      "label": "(Russian) Dub - Арт-Дубляж",
      "quality": {
        "1080": "https://...master.m3u8 or https://...master.m3u8",
        "720": "...",
        "480": "...",
        "360": "..."
      },
      "audioId": "1",
      "default": true
    },
    // ... more translations
  ],
  "tracks": [ /* subtitles */ ],
  "pnr": "wss://alloha.yani.tv/ws/",
  "pnk": "..."
}
```

### URL Deobfuscation
Each quality value contains **two mirror URLs** separated by ` or `:
```
https://mirror1.example.com/0/{path}/master.m3u8 or https://mirror2.example.com/0/{path}/master.m3u8
```

**To get a clean URL:** split on ` or ` and take the first one. No other deobfuscation needed.

---

## 7. Working Approach: Headless Browser

Since the Borth header requires executing the obfuscated JS (with multiple async steps), the reliable approach is using **Puppeteer**:

1. Fetch player HTML via `fetch()` (Node.js native)
2. Patch: remove iframe guard, remove SRI attributes
3. Use `page.setRequestInterception()` to serve patched HTML at the real URL
4. Listen for the `/bnsi/movies/` request/response
5. Extract HLS URLs from the intercepted response

This works but requires a Chromium binary (~300MB). See `test_alloha.mjs`.

---

## 8. Unresolved Questions

- **What is the prior async call that generates `yI`?** The code calls `JT()` before the Borth construction. This might be a request to another endpoint (possibly related to `pnr`/WebSocket or the `viewporti` data).
- **Can the Borth header be computed in pure Python?** Only if we can trace the full async chain in the obfuscated JS. The string array rotation makes static analysis very difficult.
- **Token lifetime:** The `token` parameter in the URL appears to expire, causing 404 responses from the API.
