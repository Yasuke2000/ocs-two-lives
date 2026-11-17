// Tensura and Not Enough Bosses bosses get a Tombstone Receptacle of Familiar like every other Tensura
// mob, so they can be summoned as allies (issue #3). Tombstone skips all of #c:capturing_not_supported,
// where Tensura and NEB list their bosses; only Tombstone's own exclusion tag drops that reference, so
// other capture mods still respect the shared tag. artifacts:mimic is the tag's only other member.
ServerEvents.tags('entity_type', event => {
  event.remove('tombstone:unhandled_tamable', '#c:capturing_not_supported')
  event.add('tombstone:unhandled_tamable', 'artifacts:mimic')
})
