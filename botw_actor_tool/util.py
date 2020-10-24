from math import ceil, isclose
from pathlib import Path
from platform import system
from typing import Union
import configparser
import os
import wx

import oead
from bcml import util as bcmlutil
from __init__ import gdata_file_prefixes, generic_link_files
from pack import ActorPack


RESIDENT_ACTORS = [
    "GameROMPlayer",
    "Dm_Npc_Gerudo_HeroSoul_Kago",
    "Dm_Npc_Goron_HeroSoul_Kago",
    "Dm_Npc_Rito_HeroSoul_Kago",
    "Dm_Npc_Zora_HeroSoul_Kago",
    "Dm_Npc_RevivalFairy",
    "PlayerStole2",
    "WakeBoardRope",
    "Armor_Default_Extra_00",
    "Armor_Default_Extra_01",
    "Item_Conductor",
    "Animal_Insect_X",
    "Animal_Insect_A",
    "Animal_Insect_B",
    "Animal_Insect_M",
    "Animal_Insect_S",
    "Explode",
    "NormalArrow",
    "FireArrow",
    "IceArrow",
    "ElectricArrow",
    "BombArrow_A",
    "AncientArrow",
    "BrightArrow",
    "BrightArrowTP",
    "RemoteBomb",
    "RemoteBomb2",
    "RemoteBombCube",
    "RemoteBombCube2",
    "Item_Magnetglove",
    "Obj_IceMakerBlock",
    "CarryBox",
    "PlayerShockWave",
    "FireRodLv1Fire",
    "FireRodLv2Fire",
    "FireRodLv2FireChild",
    "ThunderRodLv1Thunder",
    "ThunderRodLv2Thunder",
    "ThunderRodLv2ThunderChild",
    "IceRodLv1Ice",
    "IceRodLv2Ice",
    "Animal_Insect_H",
    "Animal_Insect_F",
    "Item_Material_07",
    "Item_Material_03",
    "Item_Material_01",
    "Item_Ore_F",
]
LINKS = [
    "ActorNameJpn",
    "AIProgramUser",
    "AIScheduleUser",
    "ASUser",
    "AttentionUser",
    "AwarenessUser",
    "BoneControlUser",
    "ActorCaptureUser",
    "ChemicalUser",
    "DamageParamUser",
    "DropTableUser",
    "ElinkUser",
    "GParamUser",
    "LifeConditionUser",
    "LODUser",
    "ModelUser",
    "PhysicsUser",
    "ProfileUser",
    "RgBlendWeightUser",
    "RgConfigListUser",
    "RecipeUser",
    "ShopDataUser",
    "SlinkUser",
    "UMiiUser",
    "XlinkUser",
    "AnimationInfo",
]
AAMP_LINK_REFS: dict = {
    # "ActorNameJpn",
    "AIProgramUser": ("AIProgram", ".baiprog"),
    "ASUser": ("ASList", ".baslist"),
    "AttentionUser": ("AttClientList", ".batcllist"),
    "AwarenessUser": ("Awareness", ".bawareness"),
    "BoneControlUser": ("BoneControl", ".bbonectrl"),
    # "ActorCaptureUser",
    "ChemicalUser": ("Chemical", ".bchemical"),
    "DamageParamUser": ("DamageParam", ".bdmgparam"),
    "DropTableUser": ("DropTable", ".bdrop"),
    # "ElinkUser",
    "GParamUser": ("GeneralParamList", ".bgparamlist"),
    "LifeConditionUser": ("LifeCondition", ".blifecondition"),
    "LODUser": ("LOD", ".blod"),
    "ModelUser": ("ModelList", ".bmodellist"),
    "PhysicsUser": ("Physics", ".bphysics"),
    # "ProfileUser",
    "RgBlendWeightUser": ("RagdollBlendWeight", ".brgbw"),
    "RgConfigListUser": ("RagdollConfigList", ".brgconfiglist"),
    "RecipeUser": ("Recipe", ".brecipe"),
    "ShopDataUser": ("ShopData", ".bshop"),
    # "SlinkUser",
    "UMiiUser": ("UMii", ".bumii"),
    # "XlinkUser",
}
BYML_LINK_REFS: dict = {
    "AIScheduleUser": ("AISchedule", ".baischedule"),
    "AnimationInfo": ("AnimationInfo", ".baniminfo"),
}
LANGUAGES = [
    "USen",
    "EUen",
    "USfr",
    "USes",
    "EUde",
    "EUes",
    "EUfr",
    "EUit",
    "EUnl",
    "EUru",
    "CNzh",
    "JPja",
    "KRko",
    "TWzh",
]


def _link_to_tab_index(link: str) -> int:
    # I am not proud...
    not_implemented = ["ElinkUser", "ProfileUser", "SlinkUser", "XlinkUser"]
    if link in not_implemented:
        return -1
    index = LINKS.index(link)
    if index == 0 or index == 7:
        return -1
    elif index > 7:
        return index - 1
    else:
        return index


def _try_retrieve_custom_file(link: str, fn: str) -> str:
    s = ""
    if link in generic_link_files:
        if fn in generic_link_files[link]:
            an = generic_link_files[link][fn]
            a = ActorPack(util.find_file(Path(f"Actor/Pack/{an}.sbactorpack")))
            s = a.get_link_data(link)
            del a
    return s


def _set_dark_mode(window: wx.Window, enabled: bool) -> None:
    if enabled:
        bg = wx.Colour(15, 15, 15)
        fg = wx.Colour(255, 255, 255)
    else:
        bg = wx.NullColour
        fg = wx.NullColour
    window.SetBackgroundColour(bg)
    window.SetForegroundColour(fg)
    for child in window.Children:
        _set_dark_mode(child, enabled)
    window.Refresh()


def inject_files_into_bootup(bootup_path: Path, files: list, datas: list):
    sarc_data = bootup_path.read_bytes()
    yaz = sarc_data[0:4] == b"Yaz0"
    if yaz:
        sarc_data = bcmlutil.decompress(sarc_data)
    old_sarc = oead.Sarc(sarc_data)
    del sarc_data
    new_sarc = oead.SarcWriter.from_sarc(old_sarc)
    del old_sarc
    for idx in range(len(files)):
        new_sarc.files[files[idx]] = (
            datas[idx] if isinstance(datas[idx], bytes) else bytes(datas[idx])
        )
    new_bytes = new_sarc.write()[1]
    del new_sarc
    bootup_path.write_bytes(new_bytes if not yaz else bcmlutil.compress(new_bytes))
    del new_bytes


def find_file(rel_path: Path) -> Union[Path, str]:
    settings = BatSettings()
    if rel_path.stem in RESIDENT_ACTORS:
        filepath = settings.get_setting("update_dir").replace("\\", "/")
        internal_path = str(rel_path).replace("\\", "/")
        return f"{filepath}/Pack/TitleBG.pack//{internal_path}"
    else:
        if (Path(settings.get_setting("update_dir")) / rel_path).exists():
            return Path(settings.get_setting("update_dir")) / rel_path
        elif (Path(settings.get_setting("dlc_dir")) / rel_path).exists():
            return Path(settings.get_setting("dlc_dir")) / rel_path
        elif (Path(settings.get_setting("game_dir")) / rel_path).exists():
            return Path(settings.get_setting("game_dir")) / rel_path
        else:
            raise FileNotFoundError(f"{rel_path} doesn't seem to exist.")


def unyaz_if_needed(data: bytes) -> bytes:
    if data[0:4] == b"Yaz0":
        return oead.yaz0.decompress(data)
    else:
        return data


def S32_equality(s: oead.S32, i: int) -> bool:
    return int(s) == i


def F32_equality(f: oead.F32, i: int) -> bool:
    return isclose(f, i, rel_tol=1e-5)


def FSS_equality(
    s0: Union[
        str,
        oead.FixedSafeString16,
        oead.FixedSafeString32,
        oead.FixedSafeString48,
        oead.FixedSafeString64,
        oead.FixedSafeString128,
        oead.FixedSafeString256,
    ],
    s1: str,
) -> bool:
    return str(s0) == s1


class BatSettings:
    _settings: configparser.ConfigParser

    def __init__(self) -> None:
        self._settings = configparser.ConfigParser()
        if (self.get_data_dir() / "settings.ini").exists():
            with (self.get_data_dir() / "settings.ini").open("r", encoding="utf-8") as s_file:
                self._settings.read_file(s_file)
        else:
            self._settings.read_dict(
                {
                    "General": {
                        "game_dir": "",
                        "update_dir": "",
                        "dlc_dir": "",
                        "dark_theme": False,
                        "lang": "USen",
                    },
                    "Window": {"WinPosX": "0", "WinPosY": "0", "WinHeight": "0", "WinWidth": "0",},
                }
            )

    def get_data_dir(self) -> Path:
        if system() == "Windows":
            data_dir = Path(os.path.expandvars("%LOCALAPPDATA%")) / "botw_actor_tool"
        else:
            data_dir = Path.home() / ".config" / "botw_actor_tool"
        if not data_dir.exists():
            data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir

    def set_setting(self, name: str, value: str) -> None:
        self._settings["General"][name] = value

    def get_setting(self, name: str) -> str:
        return self._settings["General"][name]

    def save_settings(self) -> None:
        settings_path = self.get_data_dir() / "settings.ini"
        with settings_path.open("w", encoding="utf-8") as s_file:
            self._settings.write(s_file)

    def set_dark_mode(self, enabled: bool) -> None:
        setting = "True" if enabled else "False"
        self.set_setting("dark_theme", setting)

    def get_dark_mode(self) -> bool:
        return True if self.get_setting("dark_theme") == "True" else False

    def get_win_pos(self) -> tuple:
        return (int(self._settings["Window"]["WinPosX"]), int(self._settings["Window"]["WinPosY"]))

    def set_win_pos(self, pos: tuple) -> None:
        if not "Window" in self._settings:
            self._settings["Window"] = {}
        self._settings["Window"]["WinPosX"] = str(pos[0])
        self._settings["Window"]["WinPosY"] = str(pos[1])

    def get_win_size(self) -> tuple:
        return (
            int(self._settings["Window"]["WinHeight"]),
            int(self._settings["Window"]["WinWidth"]),
        )

    def set_win_size(self, size: tuple) -> None:
        self._settings["Window"]["WinHeight"] = str(size[0])
        self._settings["Window"]["WinWidth"] = str(size[1])

    def validate_game_dir(self, game_path: Path) -> bool:
        if not game_path or not game_path.is_dir():
            return False
        if not (game_path / "Pack" / "Dungeon000.pack").exists():
            return False
        return True

    def validate_update_dir(self, update_path: Path) -> bool:
        if not update_path or not update_path.is_dir():
            return False
        if not (
            update_path / "Actor" / "Pack" / "ActorObserverByActorTagTag.sbactorpack"
        ).exists():
            return False
        return True

    def validate_dlc_dir(self, dlc_path: Path) -> bool:
        if not dlc_path or not dlc_path.is_dir():
            return False
        if not (dlc_path / "Pack" / "AocMainField.pack").exists():
            return False
        return True