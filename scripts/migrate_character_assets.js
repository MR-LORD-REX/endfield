const fs = require("fs");
const path = require("path");

const root = path.join(__dirname, "..");
const lines = fs.readFileSync(path.join(root, "new.js"), "utf8").split(/\r?\n/);
let chunk = lines.slice(107686, 112837).join("\n");
chunk = chunk.replace(/^\s*,\s*u1\s*=\s*/, "");
const u1 = new Function("return " + chunk)();

const fullPath = path.join(root, "src/endfield/assets/character_full.json");
const charPath = path.join(root, "src/endfield/assets/character.json");

const full = JSON.parse(fs.readFileSync(fullPath, "utf8"));
const chars = JSON.parse(fs.readFileSync(charPath, "utf8"));

const charFields = [
  "StrId",
  "NameHash",
  "Rarity",
  "Element",
  "Profession",
  "WeaponType",
  "MainAttrId",
  "SubAttrId",
  "AttributeNodes",
  "SkillInfoMap",
  "NodeSkillMap",
  "PotAttributes",
];

for (const [id, data] of Object.entries(u1)) {
  const key = String(id);
  const skillMap = data.SkillInfoMap;

  if (full[key]) {
    full[key].SkillInfoMap = skillMap;
  } else {
    full[key] = data;
  }

  if (chars[key]) {
    chars[key].SkillInfoMap = skillMap;
  } else {
    const entry = {};
    for (const field of charFields) {
      if (data[field] !== undefined) entry[field] = data[field];
    }
    chars[key] = entry;
  }
}

fs.writeFileSync(fullPath, JSON.stringify(full, null, 4) + "\n");
fs.writeFileSync(charPath, JSON.stringify(chars, null, 4) + "\n");

console.log("Updated character_full.json keys:", Object.keys(full).sort((a, b) => +a - +b).join(", "));
console.log("Updated character.json keys:", Object.keys(chars).sort((a, b) => +a - +b).join(", "));
