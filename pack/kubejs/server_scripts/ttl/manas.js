// priority: 95
// Read-only bridge to ManasCore and Tensura (design/manas-integration.md §4). There is no KubeJS plugin for
// them, so the classes are loaded by name; when an update moves one, callers get null and fall back to the
// registry's own records instead of breaking every script.
const TtlManas = {
  api: null,

  load() {
    if (this.api !== null) return this.api
    try {
      this.api = {
        skills: Java.loadClass('io.github.manasmods.manascore.skill.api.SkillAPI'),
        unique: Java.loadClass('io.github.manasmods.tensura.data.TensuraSkillTags').UNIQUE_SKILLS
      }
    } catch (e) {
      console.error(`[ttl] manas bridge unavailable: ${e}`)
      this.api = false
    }
    return this.api
  },

  // Ids of the uniques the player really holds. Negative mastery means still being learned and temporary
  // skills forget themselves, so neither counts as holding one. null when ManasCore can't be read.
  uniques(player) {
    var api = this.load()
    if (!api) return null
    try {
      var out = []
      api.skills.getSkillsFrom(player).getLearnedSkills().forEach(i => {
        if (i.is(api.unique) && i.getMastery() >= 0 && !i.isTemporarySkill()) out.push(String(i.getSkillId()))
      })
      return out
    } catch (e) {
      console.error(`[ttl] manas bridge: reading ${player.username}'s skills failed: ${e}`)
      return null
    }
  },

  // Every ability ManasCore keeps on the player, whatever its state: skills of every kind, magic, battlewill arts,
  // resistances (also the ones still being learned, negative mastery), race intrinsics and temporary skills.
  // [{id, unique, mastery, temporary}], or null when ManasCore can't be read. Used by the soul wipe (life/soul_wipe.js).
  learned(player) {
    var api = this.load()
    if (!api) return null
    try {
      var out = []
      api.skills.getSkillsFrom(player).getLearnedSkills().forEach(i => {
        out.push({ id: String(i.getSkillId()), unique: !!i.is(api.unique), mastery: Number(i.getMastery()), temporary: !!i.isTemporarySkill() })
      })
      return out
    } catch (e) {
      console.error(`[ttl] manas bridge: listing ${player.username}'s abilities failed: ${e}`)
      return null
    }
  }
}
