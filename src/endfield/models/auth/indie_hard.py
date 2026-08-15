from pydantic import BaseModel, ConfigDict, Field


class IndieHardBaseModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class KeyValue(IndieHardBaseModel):
    key: str
    value: str


class IndieHardCharacter(IndieHardBaseModel):
    char_id: str = Field(alias="charId")
    level: int
    potential_level: int = Field(alias="potentialLevel")
    avatar_url: str = Field(alias="avatarUrl")
    evolve_phase: int = Field(alias="evolvePhase")
    property: KeyValue
    rarity: KeyValue


class BestRecord(IndieHardBaseModel):
    chars: list[IndieHardCharacter]
    ts: str
    pass_ts: str = Field(alias="passTs")


class Enemy(IndieHardBaseModel):
    id: str
    name: str
    desc: str
    level: int
    image_url: str = Field(alias="imageUrl")
    ability: str


class Dungeon(IndieHardBaseModel):
    id: str
    name: str
    is_pass: bool = Field(alias="isPass")
    best_record: BestRecord | None = Field(alias="bestRecord")
    desc: str
    feature: str
    enemies: list[Enemy]
    recommend_level: int = Field(alias="recommendLevel")


class DungeonGroup(IndieHardBaseModel):
    normal_dungeon: Dungeon = Field(alias="normalDungeon")
    hard_dungeon: Dungeon = Field(alias="hardDungeon")


class AchievementData(IndieHardBaseModel):
    id: str
    name: str
    init_icon: str = Field(alias="initIcon")
    reforge2_icon: str = Field(alias="reforge2Icon")
    reforge3_icon: str = Field(alias="reforge3Icon")
    plated_icon: str = Field(alias="platedIcon")
    cate_name: str = Field(alias="cateName")
    can_certify: bool = Field(alias="canCertify")
    cate: str
    init_level: int = Field(alias="initLevel")


class Achievement(IndieHardBaseModel):
    achievement_data: AchievementData = Field(alias="achievementData")
    level: int
    is_plated: bool = Field(alias="isPlated")
    obtain_ts: str = Field(alias="obtainTs")


class IndieHardGroup(IndieHardBaseModel):
    id: str
    name: str
    pic: str
    dungeon_groups: list[DungeonGroup] = Field(alias="dungeonGroups")
    activity_start_ts: str = Field(alias="activityStartTs")
    activity_end_ts: str = Field(alias="activityEndTs")
    activity_name: str = Field(alias="activityName")
    achieve: Achievement
    is_in_activity: bool = Field(alias="isInActivity")


class IndieHard(IndieHardBaseModel):
    indie_hard_groups: list[IndieHardGroup] = Field(alias="indieHardGroups")


class IndieHardData(IndieHardBaseModel):
    indie_hard: IndieHard = Field(alias="indieHard")


__all__ = [
    "Achievement",
    "AchievementData",
    "BestRecord",
    "Dungeon",
    "DungeonGroup",
    "Enemy",
    "IndieHard",
    "IndieHardCharacter",
    "IndieHardData",
    "IndieHardGroup",
    "KeyValue",
]
