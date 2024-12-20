# Auto generated code by ssc_gen
# WARNING: Any manual changes made to this file will be lost when this
# is run again. Do not edit this file unless you know what you are doing.

from typing import List, TypedDict

from .baseStruct import BaseParser


T_MovieTranslationsPanel = TypedDict(
    "T_MovieTranslationsPanel",
    {
        "name": str,
        "value": str,
        "data_id": str,
        "data_translation_type": str,
        "data_media_hash": str,
        "data_media_type": str,
        "data_title": str,
    },
)

T_KodikAPIPayload = TypedDict(
    "T_KodikAPIPayload",
    {
        "d": str,
        "d_sign": str,
        "pd": str,
        "pd_sign": str,
        "ref": str,
        "ref_sign": str,
        "type": str,
        "hash": str,
        "id": str,
    },
)

T_KodikPage = TypedDict(
    "T_KodikPage",
    {
        "url_params": str,
        "api_payload": T_KodikAPIPayload,
        "player_js_path": str,
        "movie_translations": List["T_MovieTranslationsPanel"],
    },
)

T_KodikApiPath = TypedDict("T_KodikApiPath", {"path": str})


class MovieTranslationsPanel(BaseParser):
    """
        Representation available dubbers and params. Useful for switch dubber

    [
      {
        "name": "String",
        "value": "String",
        "data_id": "String",
        "data_translation_type": "String",
        "data_media_hash": "String",
        "data_media_type": "String",
        "data_title": "String"
      },
      "..."
    ]
    """

    def parse(self) -> List["T_MovieTranslationsPanel"]:
        return self._run_parse()

    def _run_parse(self) -> List["T_MovieTranslationsPanel"]:
        return [
            T_MovieTranslationsPanel(
                **{
                    "name": self._parse_name(el),
                    "value": self._parse_value(el),
                    "data_id": self._parse_data_id(el),
                    "data_translation_type": self._parse_data_translation_type(el),
                    "data_media_hash": self._parse_data_media_hash(el),
                    "data_media_type": self._parse_data_media_type(el),
                    "data_title": self._parse_data_title(el),
                }
            )
            for el in self._part_document(self.__selector__)
        ]

    def _part_document(self, el):
        var = self._css(el, ".movie-translations-box")
        var_1 = self._css_all(var, "option")
        return var_1

    def _parse_name(self, el):
        var = self._attr_text(el)
        var_1 = self._str_trim(var, " ")
        return var_1

    def _parse_value(self, el):
        var = self._attr(el, "value")
        return var

    def _parse_data_id(self, el):
        var = self._attr(el, "data-id")
        return var

    def _parse_data_translation_type(self, el):
        var = self._attr(el, "data-translation-type")
        return var

    def _parse_data_media_hash(self, el):
        var = self._attr(el, "data-media-hash")
        return var

    def _parse_data_media_type(self, el):
        var = self._attr(el, "data-media-type")
        return var

    def _parse_data_title(self, el):
        var = self._attr(el, "data-title")
        return var


class KodikAPIPayload(BaseParser):
    """
        payload for Kodik API request

    {
      "d": "String",
      "d_sign": "String",
      "pd": "String",
      "pd_sign": "String",
      "ref": "String",
      "ref_sign": "String",
      "type": "String",
      "hash": "String",
      "id": "String"
    }
    """

    def parse(self) -> T_KodikAPIPayload:
        return self._run_parse()

    def _run_parse(self) -> T_KodikAPIPayload:
        return T_KodikAPIPayload(
            **{
                "d": self._parse_d(self.__selector__),
                "d_sign": self._parse_d_sign(self.__selector__),
                "pd": self._parse_pd(self.__selector__),
                "pd_sign": self._parse_pd_sign(self.__selector__),
                "ref": self._parse_ref(self.__selector__),
                "ref_sign": self._parse_ref_sign(self.__selector__),
                "type": self._parse_type(self.__selector__),
                "hash": self._parse_hash(self.__selector__),
                "id": self._parse_id(self.__selector__),
            }
        )

    def _parse_d(self, el):
        var = self._attr_raw(el)
        var_1 = self._re_match(var, "var\\s*domain\\s+=\\s+['\"](.*?)['\"];", 1)
        return var_1

    def _parse_d_sign(self, el):
        var = self._attr_raw(el)
        var_1 = self._re_match(var, "var\\s*d_sign\\s+=\\s+['\"](.*?)['\"];", 1)
        return var_1

    def _parse_pd(self, el):
        var = self._attr_raw(el)
        var_1 = self._re_match(var, "var\\s*pd\\s+=\\s+['\"](.*?)['\"];", 1)
        return var_1

    def _parse_pd_sign(self, el):
        var = self._attr_raw(el)
        var_1 = self._re_match(var, "var\\s*pd_sign\\s+=\\s+['\"](.*?)['\"];", 1)
        return var_1

    def _parse_ref(self, el):
        var = self._attr_raw(el)
        var_1 = self._re_match(var, "var\\s*ref\\s+=\\s+['\"](.*?)['\"];", 1)
        return var_1

    def _parse_ref_sign(self, el):
        var = self._attr_raw(el)
        var_1 = self._re_match(var, "var\\s*ref_sign\\s+=\\s+['\"](.*?)['\"];", 1)
        return var_1

    def _parse_type(self, el):
        var = self._attr_raw(el)
        var_1 = self._re_match(var, "videoInfo\\.type\\s*=\\s*['\"](.*?)['\"];", 1)
        return var_1

    def _parse_hash(self, el):
        var = self._attr_raw(el)
        var_1 = self._re_match(var, "videoInfo\\.hash\\s*=\\s*['\"](.*?)['\"];", 1)
        return var_1

    def _parse_id(self, el):
        var = self._attr_raw(el)
        var_1 = self._re_match(var, "videoInfo\\.id\\s*=\\s*['\"](.*?)['\"];", 1)
        return var_1


class KodikPage(BaseParser):
    """
        this schema used to extract params for next API request

        required next keys for API request:
            - contain in `api_payload` key
        constants:
            - cdn_is_working: true
            - bad_user: false (or true)
            - info: {}

        USAGE:
            1. GET <PLAYER_LINK> (e.g.: https://kodik.info/seria/1133512/04d5f7824ba3563bd78e44a22451bb45/720p)
            2. parse payload (see required pairs upper) (<PAYLOAD>)
            3. extract the API path from player_js_path (<API_PATH>) (encoded in BASE64)
            4. POST https://kodik.info/ + <API_PATH>; data=<PAYLOAD> (<JSON>). next HEADERS required:
                - origin="https://<NETLOC>" // player page
                - referer=<PLAYER_LINK> // FIRST URL player entrypoint
                - accept= "application/json, text/javascript, */*; q=0.01"
            5. extract data from ['links'] key from <JSON> response
            6. urls encoded in ROT_13 + BASE64 ciphers
        ISSUES:
            - kodik maybe have another netloc (e.g.: anivod)
            - 403 Forbidden if request sent not from CIS region
            - 404 DELETED: eg: https://kodik.info/seria/310427/09985563d891b56b1e9b01142ae11872/720p
            - 500 Internal server error: eg: https://kodik.info/seria/1051016/af405efc5e061f5ac344d4811de3bc16/720p ('Cyberpunk: Edgerunners' ep5 Anilibria dub)



    {
      "url_params": "String",
      "api_payload": {
        "d": "String",
        "d_sign": "String",
        "pd": "String",
        "pd_sign": "String",
        "ref": "String",
        "ref_sign": "String",
        "type": "String",
        "hash": "String",
        "id": "String"
      },
      "player_js_path": "String",
      "movie_translations": [
        {
          "name": "String",
          "value": "String",
          "data_id": "String",
          "data_translation_type": "String",
          "data_media_hash": "String",
          "data_media_type": "String",
          "data_title": "String"
        },
        "..."
      ]
    }
    """

    def parse(self) -> T_KodikPage:
        return self._run_parse()

    def _run_parse(self) -> T_KodikPage:
        return T_KodikPage(
            **{
                "url_params": self._parse_url_params(self.__selector__),
                "api_payload": self._parse_api_payload(self.__selector__),
                "player_js_path": self._parse_player_js_path(self.__selector__),
                "movie_translations": self._parse_movie_translations(self.__selector__),
            }
        )

    def _parse_url_params(self, el):
        var = self._attr_raw(el)
        var_1 = self._re_match(var, "var\\s*urlParams\\s*=\\s*['\"](\\{.*\\})['\"]", 1)
        return var_1

    def _parse_api_payload(self, el):
        var = self._nested_parser(el, KodikAPIPayload)
        return var

    def _parse_player_js_path(self, el):
        var = self._attr_raw(el)
        var_1 = self._re_match(
            var, '<script\\s*type="text/javascript"\\s*src="(/assets/js/app\\.player_single.*?)">', 1
        )
        return var_1

    def _parse_movie_translations(self, el):
        try:
            var = self._nested_parser(el, MovieTranslationsPanel)
            return var
        except Exception:
            return None


class KodikApiPath(BaseParser):
    """
        Extract the API path from js player source

    {
      "path": "String"
    }
    """

    def parse(self) -> T_KodikApiPath:
        return self._run_parse()

    def _run_parse(self) -> T_KodikApiPath:
        return T_KodikApiPath(
            **{
                "path": self._parse_path(self.__selector__),
            }
        )

    def _parse_path(self, el):
        var = self._attr_raw(el)
        var_1 = self._re_match(var, "\\$\\.ajax\\([^>]+,url:\\s*atob\\([\"']([\\w=]+)[\"']\\)", 1)
        return var_1
