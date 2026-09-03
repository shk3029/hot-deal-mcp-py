from __future__ import annotations

import os
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Mapping, Optional, Callable, Any, Dict, Literal

import httpx, yaml, json, random, string, re

########################  표준 전문 헤더 생성을 위한 Util - START #############################
FieldType = Literal["NUM", "TXT"]

@dataclass(frozen=True)
class FieldSpec:
    name: str
    length: int
    ftype: FieldType
    align: Literal["l","r"] = "r"
    default: str | None = None

def _byte_len(s: str, encoding: str = "utf-8") -> int:
    return len(s.encode(encoding))

def pad_number(value: int | str, total_len : int, align: str = "r") -> str:
    """
    숫자 필드 패딩:
    - align = "r" : 오른쪽 정렬, 왼쪽 0 패딩 (예: 123 -> 000123)
    - align = "l" : 왼쪽 정렬, 오른쪽 0 패딩 (예: 123 -> 123000)
    - total_len : byte 길이 강제
    """
    if align not in ("l","r"):
        raise ValueError("align must be 'l' or 'r'")

    s = str(value)
    if not s.isdigit():
        raise ValueError(f"Number field must contain digits only: {s!r}")

    if _byte_len(s) > total_len:
        raise ValueError(f"Value too long in bytes: {s!r} (bytes={_byte_len(s)}) > (total_len={total_len})")

    pad_count = total_len - _byte_len(s)
    if align == "r":
        return ("0" * pad_count) + s
    return s + ("0" * pad_count)

def pad_text(value: str, total_len : int, align: str = "r") -> str:
    """
    문자 필드 패딩:
    - align = "r" : 오른쪽 정렬, 왼쪽 " " 패딩 (예: SHC -> "SHC   ")
    - align = "l" : 왼쪽 정렬, 오른쪽 " " 패딩 (예: SHC -> "   SHC")
    - total_len : byte 길이 강제
    """
    if align not in ("l","r"):
        raise ValueError("align must be 'l' or 'r'")

    s = value if value is not None else ""

    if _byte_len(s) > total_len:
        raise ValueError(f"Value too long in bytes: {s!r} (bytes={_byte_len(s)}) > (total_len={total_len})")

    pad_count = total_len - _byte_len(s)
    if align == "r":
        return (" " * pad_count) + s
    return s + (" " * pad_count)

def now_hhmmss(tz: str = "Asia/Seoul") -> str:
    dt = datetime.now(ZoneInfo(tz))
    return dt.strftime("%H%M%S")

def now_hhmmssSS(tz: str = "Asia/Seoul") -> str:
    dt = datetime.now(ZoneInfo(tz))
    centi = dt.microsecond // 10_000
    return dt.strftime("%H%M%S") + f"{centi:02d}"

def now_yyyyMMdd(tz: str = "Asia/Seoul") -> str:
    dt = datetime.now(ZoneInfo(tz))
    return dt.strftime("%Y%m%d")

def uid14(tz: str = "Asia/Seoul") -> str:
    """
    14자리 영숫자 유니크값 생성

    형식:
        MMddHHmmss(10자리 숫자)
        + 랜덤 영숫자 4자리

    예:
        260226143012A7
    """
    now = datetime.now(ZoneInfo(tz))
    time_part = now.strftime("%m%d%H%M%S")
    rand_part = "".join(random.choices(string.ascii_uppercase+string.ascii_lowercase + string.digits, k=4))
    return time_part + rand_part

def _parse_num(raw_value: str, align: str, strip_num_padding: bool) -> str:
    if not strip_num_padding:
        return raw_value

    if align == "r":
        value = raw_value.lstrip("0")
    if align == "l":
        value = raw_value.rstrip("0")
    else:
        value = raw_value.strip("0")

    return value if value != "" else "0"

def build_fixed_message_from_specs(specs: list[FieldSpec], values: dict[str, Any]) -> str:
    values.update({
        "TG_WRT_D": now_yyyyMMdd(),
        "SDD_TG_SRL_N": uid14(),
        "NI_TG_RQ_DT": now_yyyyMMdd()+now_hhmmssSS()
    })
    parts: list[str] = []
    for sp in specs:
        raw = values.get(sp.name)
        if sp.ftype == "NUM":
            if raw is None:
                val = sp.default if sp.default is not None else "0"
            else:
                val = raw
            val_str = str(val)
            if not val_str.isdigit():
                raise ValueError(f"{sp.name} must be number. got={val_str}")
            parts.append(pad_number(val_str, sp.length, align=sp.align))
            continue
        elif sp.ftype == "TXT":
            if raw is None:
                val = sp.default if sp.default is not None else ""
            else:
                val = raw
            val_str = str(val)
            parts.append(pad_text(val_str, sp.length, align=sp.align))
            continue
        else:
            raise ValueError(f'Unknown field type: {sp.ftype}')
    return "".join(parts)

def build_json_from_fixed_message(message: str,
                                  specs: list[FieldSpec],
                                  *,
                                  encoding: str = "utf-8",
                                  strip_text: bool = True,
                                  strip_num_padding: bool = True,
                                  num_as_int: bool = False,
                                 ) -> dict[str, Any]:
    message_bytes = message.encode(encoding)
    expected_len = sum(spec.length for spec in specs)

    if len(message_bytes) != expected_len:
        raise ValueError(
            f"message byte length mismatch: expected={expected_len}, input={len(message_bytes)}"
        )

    result: dict[str, Any] = {}
    offset = 0

    for spec in specs:
        raw_value = message_bytes[offset:offset + spec.length].decode(encoding)

        if spec.ftype == "TXT":
            value = raw_value.strip() if strip_text else raw_value

        elif spec.ftype == "NUM":
            value = _parse_num(raw_value, spec.align, strip_num_padding)
            if num_as_int:
                value = int(value)

        else:
            raise ValueError(f"Unsupported field type: {spec.ftype}")

        result[spec.name] = value
        offset += spec.length

    return result

SYS_CMN_SPEC = [
    #SDD_TG_LTH 표준전문길이는 587 Byte 고정
    FieldSpec("SDD_TG_LTH", 8, "NUM", align="r"),
    #TG_ECR_CCD 전문암호화 구분코드
    # "0"-사용안함, "1"-SEED, "2"-3DES
    FieldSpec("TG_ECR_CCD", 1, "TXT", align="r"),
    #SH_GP_CO_CD 그룹사코드 "S012"-신한카드
    FieldSpec("SH_GP_CO_CD", 4, "TXT", align="r"),
    #TG_WRT_D 전문작성일 - now_yyyyMMdd() 사용
    FieldSpec("TG_WRT_D", 8, "TXT", align="r"),
    #TG_CRT_SYS_NM 전문생성시스템명
    FieldSpec("TG_CRT_SYS_NM", 8, "TXT", align="l"),
    #SDD_TG_SRL_N 표준전문시리얼번호 - uid14() 사용
    FieldSpec("SDD_TG_SRL_N", 14, "TXT", align="r"),
    #SDD_TG_PGS_N 표준전문진행번호 - 항상 00
    FieldSpec("SDD_TG_PGS_N", 2, "NUM", align="r"),
    FieldSpec("TG_IP_AR", 32, "TXT", align="r"),
    FieldSpec("TG_MAC_AR", 12, "TXT", align="r"),
    #EVN_IF_CCD 환경 정보 구분코드
    #"D"=개발,"T"=테스트,"R"운영
    FieldSpec("EVN_IF_CCD", 1, "TXT", align="r"),
    #NI_TI_BNE_CCD 최초전송시스템업무구분코드
    FieldSpec("NI_TI_BNE_CCD", 3, "TXT", align="r"),
    #TI_BNE_CCD 전송시스템업무구분코드
    FieldSpec("TI_BNE_CCD", 3, "TXT", align="r"),
    FieldSpec("TI_NOD_N", 4, "NUM", align="r"),
    FieldSpec("XAC_TS_CCD", 1, "TXT", align="r"),
    #RQ_SO_CCD 요청응답구분코드 - 항상 요청(S)
    FieldSpec("RQ_SO_CCD", 1, "TXT", align="r"),
    FieldSpec("TS_MTV_CCD", 1, "TXT", align="r"),
    #NI_TG_RQ_DT 최초전문요청일시 - now_yyyyMMdd()+now_hhmmssSS() 사용
    FieldSpec("NI_TG_RQ_DT", 16, "TXT", align="r"),
    FieldSpec("TTL_SE_CCD", 1, "TXT", align="r"),
    FieldSpec("NI_SR_TM", 6, "TXT", align="r"),
    FieldSpec("MTN_HMS", 3, "NUM", align="r"),
    FieldSpec("RP_SV_CD", 12, "TXT", align="r"),
    FieldSpec("RU_RP_SV_CD", 12, "TXT", align="r"),
    FieldSpec("RLT_SV_CD", 12, "TXT", align="r"),
    FieldSpec("EAI_ITF_ID", 16, "TXT", align="r"),
    FieldSpec("TG_SO_DT", 16, "TXT", align="r"),
    FieldSpec("PS_RU_CCD", 1, "TXT", align="r"),
    FieldSpec("OUT_TG_TP_CD", 1, "TXT", align="r"),
    FieldSpec("NI_ER_BNE_CCD", 3, "TXT", align="r"),
    FieldSpec("NI_SYS_ER_KCD", 2, "TXT", align="r"),
    FieldSpec("NI_SDD_TG_ERR_CD", 8, "TXT", align="r"),
    FieldSpec("TG_VER_CCD", 3, "TXT", align="r"),
    FieldSpec("LAG_CCD", 1, "NUM", align="r"),
    FieldSpec("OM_TS_F", 1, "TXT", align="r"),
    FieldSpec("MCI_NOD_N", 2, "TXT", align="r"),
    FieldSpec("MCI_SSS_ID_N", 8, "TXT", align="r"),
    FieldSpec("SMU_TS_CD", 1, "TXT", align="r"),
    FieldSpec("TST_CMI_RLB_CD", 1, "TXT", align="r"),
    FieldSpec("CLCT_F", 1, "TXT", align="r"),
    FieldSpec("SYS_HDR_PPR_ITM", 54, "TXT", align="r"),
    FieldSpec("TG_MSG_TP_CD", 1, "TXT", align="r"),
    FieldSpec("PCK_EN", 8, "TXT", align="r"),
    FieldSpec("PCK_DCD", 4, "TXT", align="r"),
    FieldSpec("PCK_DTY_CD", 5, "TXT", align="r"),
    FieldSpec("PCK_JBT_CD", 5, "TXT", align="r"),
    FieldSpec("PCK_KEY_N", 3, "TXT", align="r"),
    FieldSpec("PCK_OPS_HCD", 4, "NUM", align="r"),
    FieldSpec("APV_K_CN", 1, "NUM", align="r"),
    FieldSpec("PMY_APV_K_DCD", 4, "TXT", align="r"),
    FieldSpec("PMY_APV_K_EN", 8, "TXT", align="r"),
    FieldSpec("PMY_APV_K_DTY_CD", 5, "TXT", align="r"),
    FieldSpec("PMY_APV_K_JBT_CD", 5, "TXT", align="r"),
    FieldSpec("PMY_APV_K_KEY_N", 3, "TXT", align="r"),
    FieldSpec("SDY_APV_K_DCD", 4, "TXT", align="r"),
    FieldSpec("SDY_APV_K_EN", 8, "TXT", align="r"),
    FieldSpec("SDY_APV_K_DTY_CD", 5, "TXT", align="r"),
    FieldSpec("SDY_APV_K_JBT_CD", 5, "TXT", align="r"),
    FieldSpec("SDY_APV_K_KEY_N", 3, "TXT", align="r"),
    FieldSpec("SH_SCE_N", 10, "TXT", align="r"),
    FieldSpec("ITF_ID", 8, "TXT", align="r"),
    FieldSpec("BX_TS_CD", 4, "TXT", align="r"),
    FieldSpec("BK_TMN_ILL_BN_N", 4, "NUM", align="r"),
    FieldSpec("BK_TMN_ILL_ISM_N", 4, "TXT", align="r"),
    FieldSpec("BK_TMN_TS_RQ_SRL_N", 8, "NUM", align="r"),
    FieldSpec("BK_TS_BN_N", 4, "NUM", align="r"),
    FieldSpec("BK_TS_BN_ISM_N", 4, "NUM", align="r"),
    FieldSpec("BK_BNB_PRT_CNC_N", 1, "TXT", align="r"),
    FieldSpec("BK_TMN_RP_BE_CD", 1, "NUM", align="r"),
    FieldSpec("BK_CLO_CD", 1, "NUM", align="r"),
    FieldSpec("BK_ISM_ILL_GP_CD", 4, "TXT", align="r"),
    FieldSpec("BK_MDA_CCD", 8, "TXT", align="r"),
    FieldSpec("BK_BNE_BEG_CCD", 1, "NUM", align="r"),
    FieldSpec("BK_TNS_NOD_CCD", 5, "TXT", align="r"),
    FieldSpec("BK_SVC_NR_BN_N", 4, "NUM", align="r"),
    FieldSpec("BK_WND_CD", 2, "NUM", align="r"),
    FieldSpec("BK_SI_OR_CCD", 1, "TXT", align="r"),
    FieldSpec("BK_SCE_PUT_EVN_CCD", 1, "TXT", align="r"),
    FieldSpec("BK_SCE_PUT_SCA_N", 4, "TXT", align="r"),
    FieldSpec("BK_SCE_PUT_PCI_ATI_N", 2, "TXT", align="r"),
    FieldSpec("BK_ARY_BN_N", 4, "NUM", align="r"),
    FieldSpec("BK_BSN_BN_N", 4, "NUM", align="r"),
    FieldSpec("BK_CSL_EN", 8, "TXT", align="r"),
    FieldSpec("BK_UFC_CHL_USR_MSG_OUT_CD", 1, "NUM", align="r"),
    FieldSpec("BK_CHL_TCD", 2, "TXT", align="r"),
    FieldSpec("ARS_CIB_ID", 20, "TXT", align="r"),
    FieldSpec("ARS_SCA_CD", 6, "TXT", align="r"),
    FieldSpec("EDI_TG_CHL_ID", 16, "TXT", align="r"),
    FieldSpec("CE_TS_C_VL", 1, "TXT", align="r"),
    FieldSpec("CRR_TS_C_VL", 1, "TXT", align="r"),
    FieldSpec("QY_KEY_C_VL", 1, "TXT", align="r"),
    FieldSpec("QY_KEY_VL", 19, "TXT", align="r"),
    FieldSpec("NXT_QY_F", 1, "TXT", align="r"),
    FieldSpec("SCF_CLN_CF_VL", 1, "TXT", align="r"),
    FieldSpec("RQ_TS_CCD", 1, "TXT", align="r"),
    FieldSpec("TS_COM_PPR_ITM", 55, "TXT", align="r"),
]
DATA_SPEC = [
    FieldSpec("DATA_TDA_KCD", 2, "TXT", align="r"),
    FieldSpec("DATA_TDA_LTH", 8, "NUM", align="r"),
    FieldSpec("DATA_TS_CD", 12, "TXT", align="l"),
    FieldSpec("DATA_SH_SCE_N", 10, "TXT", align="r"),
    FieldSpec("FRM_PEA_TN", 2, "TXT", align="r"),
]
########################  표준 전문 헤더 생성을 위한 Util - END #############################

########################  mci-interface 로드를 위한 Util - START #############################
@dataclass(frozen=True)
class InterfaceSpec:
    path: str
    rp_sv_cd: str
    target: str
    env: str
    eai_id: str
    masking: list[dict[str, Any]] = field(default_factory=list)

@dataclass(frozen=True)
class ClientSettings:
    base_dev_url: Dict[str, str]
    base_test_url: Dict[str, str]
    base_prd_url: Dict[str, str]
    interface_map: Dict[str, InterfaceSpec]

def load_client_settings(config_path: str | Path) -> ClientSettings:
    try:
        path = Path(config_path)
        with path.open("r", encoding="utf-8") as file:
            raw = yaml.safe_load(file)

        base_dev_url = raw["base_dev_url"]
        base_test_url = raw["base_test_url"]
        base_prd_url = raw["base_prd_url"]
        interface_section = raw.get("interfaces", {})
        masking_presets = raw.get("masking_presets", [])

        interface_map: Dict[str, InterfaceSpec] = {}
        for interface_name, spec in interface_section.items():
            interface_map[interface_name] = InterfaceSpec(
                path=spec["path"],
                rp_sv_cd=spec["rp_sv_cd"],
                target=spec["target"],
                env=spec["env"],
                eai_id=spec["eai_id"],
                masking=masking_presets,
            )

        return ClientSettings(
            base_dev_url=base_dev_url,
            base_test_url=base_test_url,
            base_prd_url=base_prd_url,
            interface_map=interface_map
        )
    except Exception as exc:
        #log 처리
        raise

########################  mci-interface 로드를 위한 Util - END #############################

########################  MCI Client에 대한 정의 - START #############################
class MciClient:
    def __init__(
        self,
        config_path: str = os.path.join(os.getenv("SVC_CONFIG_DIR", "/project/work/flow/config/dev"), "mci_interfaces.yaml"),
        timeout: Optional[float] = 60.0,
        shc_header_values: Mapping[str, Any] | None = None,
        data_header_values: Mapping[str, Any] | None = None,
    ) -> None:
        self._timeout = timeout
        self._settings: ClientSettings = load_client_settings(config_path)
        self.shc_header_values: dict[str, Any] = {
            "SDD_TG_LTH": 587,
            "TG_ECR_CCD": "0",
            "SH_GP_CO_CD": "S012",
            "TG_WRT_D": now_yyyyMMdd(),
            "TG_CRT_SYS_NM": "GEN",
            "SDD_TG_SRL_N": uid14(),
            "SDD_TG_PGS_N": 0,
            "NI_TI_BNE_CCD": "GEN",
            "TI_BNE_CCD": "GEN",
            "XAC_TS_CCD": "0",
            "RQ_SO_CCD": "S",
            "NI_TG_RQ_DT": now_yyyyMMdd()+now_hhmmssSS(),
            "TG_VER_CCD": "R10",
        }
        self.shc_header_values.update(dict(shc_header_values or {}))

        self.data_header_values: dict[str, Any] = {
            "DATA_TDA_KCD": 90,
            "FRM_PEA_TN": "00"
        }
        self.data_header_values.update(dict(data_header_values or {}))

        _ = build_fixed_message_from_specs(SYS_CMN_SPEC, self.shc_header_values)
        # print(f'sys + cmn header \n {_}')
        _ = build_fixed_message_from_specs(DATA_SPEC, self.data_header_values)
        # print(f'data header \n{_}')


    # @property
    # def base_url(self) -> str:
    #     return self._settings.base_url

    # @property
    # def base_test_url(self) -> str:
    #     return self._settings.base_test_url

    # def _build_url(self, path: str) -> str:
    #     return f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"

    # def _build_test_url(self, path: str) -> str:
    #     return f"{self.base_test_url.rstrip('/')}/{path.lstrip('/')}"

    def _build_url(self, path:str ="/", env: str="D", target: str="internal") -> str:
        if env == "R":
            return f"{self._settings.base_prd_url[target].rstrip('/')}/{path.lstrip('/')}"
        elif env == "T":
            return f"{self._settings.base_test_url[target].rstrip('/')}/{path.lstrip('/')}"
        else:
            return f"{self._settings.base_dev_url[target].rstrip('/')}/{path.lstrip('/')}"

    def _get_interface_spec(self, interface_name: str) -> InterfaceSpec:
        spec = self._settings.interface_map.get(interface_name)
        if spec is None:
            # raise Exception
            raise
        return spec

    def _parse_response(self, response: httpx.Response) -> dict:
        try:
            raw_text = response.text
            parsed = json.loads(raw_text)

            data = parsed.get("DATA")
            message = parsed.get("MESSAGE")
            data_header = parsed.get("DATA-HEADER")

            if data is not None:
                return data

            error_code = message
            return error_code
        except Exception as exc:
            raise

    def _build_mask_idx(self, masking: list[dict[str, Any]]) -> dict[str, list[tuple[re.Pattern, str]]]:
        idx: dict[str,list[tuple[re.Pattern, str]]] = {}
        for mask_rule in masking:
            field_name = mask_rule.get("field")
            pattern = mask_rule.get("pattern")
            repl = mask_rule.get("repl")

            if not field_name or not pattern or repl is None:
                continue

            try:
                compiled = re.compile(pattern)
            except e:
                continue
            idx.setdefault(field_name, []).append((compiled, repl))
        return idx

    def _mask_value(self,
                    value: Any,
                    rules: list[tuple[re.Pattern, str]] | None = None) -> Any:

        if value is None:
            return value

        text = str(value)

        for pattern, repl in rules:
            if pattern.search(text):
                text = pattern.sub(repl, text)

        return text


    def _mask_response(self,
                       response: Any | None = None,
                       masking: list[dict[str, Any]] | None = None) -> dict:
        """
            데이터 마스킹 처리
        """
        if response is None:
            return response

        if not isinstance(response, dict):
            return response

        mask_idx = self._build_mask_idx(masking)

        if not mask_idx:
            return response

        target_fields = set(mask_idx.keys())

        def _mask(obj: Any) -> Any:
            if isinstance(obj, dict):
                masked: dict[Any, Any] = {}

                for key, value in obj.items():
                    if key in target_fields:
                        masked[key] = self._mask_value(value, mask_idx[key])
                    elif isinstance(value, dict):
                        masked[key] = _mask(value)
                    elif isinstance(value, list):
                        masked[key] = _mask(value)
                    else:
                        masked[key] = value
                return masked
            if isinstance(obj, list):
                return [
                    _mask(item) if isinstance(item, (dict, list)) else item for item in obj
                ]
            return obj

        try:
            return _mask(response)
        except Exception as e:
            raise ValueError(f"error with masking value {response}")
            return masked


    def call(self,
             path: str,
             target: str,
             input_sys_header: Mapping[str, Any] | None = None,
             input_data_header: Mapping[str, Any] | None = None,
             data: Any | None = None,
            ):
        try:
            default_sys_header = {
                "TS_MTV_CCD": "S"
            }
            if input_sys_header is None:
                input_sys_header = {}
            input_sys_header.update(default_sys_header)
            input_sys_header.update(self.shc_header_values)

            if input_data_header is None:
                input_data_header = {}
            input_data_header.update(self.data_header_values)

            call_sys_header_str = build_fixed_message_from_specs(SYS_CMN_SPEC, input_sys_header)
            call_data_header_str = build_fixed_message_from_specs(DATA_SPEC, input_data_header)


            if input_sys_header.get("EVN_IF_CCD") is not None:
                url = self._build_url(path=path, env=input_sys_header.get("EVN_IF_CCD"), target=target)
            else:
                raise ValueError

            headers = {
                "Content-Type": "application/json; charset=utf-8",
                "shc-header": call_sys_header_str+";",
            }

            payload = {
                "DATA-HEADER": call_data_header_str,
                "DATA": data,
            }

            print(headers)
            print(payload)
            print(url)

            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(url=url, headers=headers, json=payload)
                response.raise_for_status()
                # print("=========")
                # print(response.text)
                # print("=========")
                return self._parse_response(response)
        except Exception as exc:
            raise


    def call_with_itf_id(self,
                         itf_id: str,
                         data: Any | None = None,
                         include_sensitive: boolean = False):
        try:
            spec = self._get_interface_spec(itf_id)

            input_sys_header: dict[str, Any] = {
                "EVN_IF_CCD": spec.env,
                "ITF_ID": itf_id,
                "RP_SV_CD": spec.rp_sv_cd,
                "EAI_ITF_ID": spec.eai_id,
            }
            input_data_header: dict[str, Any] = {
                "DATA_TS_CD": spec.rp_sv_cd,
            }
            response = self.call(path=spec.path,
                                 target=spec.target,
                                 input_sys_header=input_sys_header,
                                 input_data_header=input_data_header,
                                 data=data)

            if not include_sensitive:
                response = self._mask_response(response=response,
                                               masking=spec.masking)

            return response
        except Exception as exc:
            raise

    def call_raw(self,
             path: str,
             target: str,
             input_sys_header: Mapping[str, Any] | None = None,
             input_data_header: Mapping[str, Any] | None = None,
             data: Any | None = None,
            ):
        try:
            default_sys_header = {
                "TS_MTV_CCD": "S"
            }
            if input_sys_header is None:
                input_sys_header = {}
            input_sys_header.update(default_sys_header)
            input_sys_header.update(self.shc_header_values)

            if input_data_header is None:
                input_data_header = {}
            input_data_header.update(self.data_header_values)

            call_sys_header_str = build_fixed_message_from_specs(SYS_CMN_SPEC, input_sys_header)
            call_data_header_str = build_fixed_message_from_specs(DATA_SPEC, input_data_header)


            if input_sys_header.get("EVN_IF_CCD") is not None:
                url = self._build_url(path=path, env=input_sys_header.get("EVN_IF_CCD"), target=target)
            else:
                raise ValueError

            headers = {
                "Content-Type": "application/json; charset=utf-8",
                "shc-header": call_sys_header_str+";",
            }

            payload = {
                "DATA-HEADER": call_data_header_str,
                "DATA": data,
            }

            print(headers)
            print(payload)
            print(url)

            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(url=url, headers=headers, json=payload)
                response.raise_for_status()
                # print("=========")
                # print(response.text)
                # print("=========")
                # return self._parse_response(response)
                return response
        except Exception as exc:
            raise


    def call_with_itf_id_raw(self,
                         itf_id: str,
                         data: Any | None = None,
                         include_sensitive: boolean = False):
        try:
            spec = self._get_interface_spec(itf_id)

            input_sys_header: dict[str, Any] = {
                "EVN_IF_CCD": spec.env,
                "ITF_ID": itf_id,
                "RP_SV_CD": spec.rp_sv_cd,
                "EAI_ITF_ID": spec.eai_id,
            }
            input_data_header: dict[str, Any] = {
                "DATA_TS_CD": spec.rp_sv_cd,
            }
            response = self.call_raw(path=spec.path,
                                 target=spec.target,
                                 input_sys_header=input_sys_header,
                                 input_data_header=input_data_header,
                                 data=data)
            if response is None:
                raise ValueError(f"error with response is None")

            res_header = response.headers.get("shc-header")
            if res_header is None:
                raise ValueError(f"error with response shc_header is None")

            res_header = res_header.replace(";","")
            ret_header_json = build_json_from_fixed_message(res_header,SYS_CMN_SPEC)
            ret_response = self._parse_response(response)


            if not include_sensitive:
                ret_response = self._mask_response(response=ret_response,
                                               masking=spec.masking)

            return {"data":ret_response, "header":ret_header_json}
        except Exception as exc:
            raise

    async def acall(self,
                    path: str,
                    target: str,
                    input_sys_header: Mapping[str, Any] | None = None,
                    input_data_header: Mapping[str, Any] | None = None,
                    data: Any| None = None
                    ):
        try:

            default_sys_header = {
                "TS_MTV_CCD": "A"
            }

            if input_sys_header is None:
                input_sys_header = {}
            input_sys_header.update(default_sys_header)
            input_sys_header.update(self.shc_header_values)

            if input_data_header is None:
                input_data_header = {}
            input_data_header.update(self.data_header_values)

            call_sys_header_str = build_fixed_message_from_specs(SYS_CMN_SPEC, input_sys_header)
            call_data_header_str = build_fixed_message_from_specs(DATA_SPEC, input_data_header)

            if input_sys_header.get("EVN_IF_CCD") is not None:
                url = self._build_url(path=path, env=input_sys_header.get("EVN_IF_CCD"), target=target)
            else:
                raise ValueError

            headers = {
                "Content-Type": "application/json; charset=utf-8",
                "shc-header": call_sys_header_str+";",
            }

            payload = {
                "DATA-HEADER": call_data_header_str,
                "DATA": data,
            }

            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(url=url, headers=headers, json=payload)
                response.raise_for_status()
                return self._parse_response(response)
        except Exception as exc:
            raise

    async def acall_with_itf_id(self,
                                 itf_id: str,
                                 data: Any | None = None,
                                 include_sensitive: boolean = False
                                ):
        try:
            spec = self._get_interface_spec(itf_id)
            input_sys_header: dict[str, Any] = {
                "EVN_IF_CCD": spec.env,
                "ITF_ID": itf_id,
                "RP_SV_CD": spec.rp_sv_cd,
                "EAI_ITF_ID": spec.eai_id,
            }
            input_data_header: dict[str, Any] = {
                "DATA_TS_CD": spec.rp_sv_cd,
            }
            response = await self.acall(path=spec.path,
                                       target=spec.target,
                                       input_sys_header=input_sys_header,
                                       input_data_header=input_data_header,
                                       data=data)

            if not include_sensitive:
                response = self._mask_response(response=response,
                                               masking=spec.masking)

            return response
        except Exception as exc:
            raise

    async def acall_raw(self,
             path: str,
             target: str,
             input_sys_header: Mapping[str, Any] | None = None,
             input_data_header: Mapping[str, Any] | None = None,
             data: Any | None = None,
            ):
        try:
            default_sys_header = {
                "TS_MTV_CCD": "S"
            }
            if input_sys_header is None:
                input_sys_header = {}
            input_sys_header.update(default_sys_header)
            input_sys_header.update(self.shc_header_values)

            if input_data_header is None:
                input_data_header = {}
            input_data_header.update(self.data_header_values)

            call_sys_header_str = build_fixed_message_from_specs(SYS_CMN_SPEC, input_sys_header)
            call_data_header_str = build_fixed_message_from_specs(DATA_SPEC, input_data_header)


            if input_sys_header.get("EVN_IF_CCD") is not None:
                url = self._build_url(path=path, env=input_sys_header.get("EVN_IF_CCD"), target=target)
            else:
                raise ValueError

            headers = {
                "Content-Type": "application/json; charset=utf-8",
                "shc-header": call_sys_header_str+";",
            }

            payload = {
                "DATA-HEADER": call_data_header_str,
                "DATA": data,
            }

            print(headers)
            print(payload)
            print(url)

            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(url=url, headers=headers, json=payload)
                response.raise_for_status()
                # print("=========")
                # print(response.text)
                # print("=========")
                # return self._parse_response(response)
                return response
        except Exception as exc:
            raise


    async def acall_with_itf_id_raw(self,
                         itf_id: str,
                         data: Any | None = None,
                         include_sensitive: boolean = False):
        try:
            spec = self._get_interface_spec(itf_id)

            input_sys_header: dict[str, Any] = {
                "EVN_IF_CCD": spec.env,
                "ITF_ID": itf_id,
                "RP_SV_CD": spec.rp_sv_cd,
                "EAI_ITF_ID": spec.eai_id,
            }
            input_data_header: dict[str, Any] = {
                "DATA_TS_CD": spec.rp_sv_cd,
            }
            response = await self.acall_raw(path=spec.path,
                                 target=spec.target,
                                 input_sys_header=input_sys_header,
                                 input_data_header=input_data_header,
                                 data=data)
            if response is None:
                raise ValueError(f"error with response is None")

            res_header = response.headers.get("shc-header")
            if res_header is None:
                raise ValueError(f"error with response shc_header is None")

            res_header = res_header.replace(";","")
            ret_header_json = build_json_from_fixed_message(res_header,SYS_CMN_SPEC)
            ret_response = self._parse_response(response)


            if not include_sensitive:
                ret_response = self._mask_response(response=ret_response,
                                               masking=spec.masking)

            return {"data":ret_response, "header":ret_header_json}
        except Exception as exc:
            raise


########################  MCI Client에 대한 정의 - END #############################
