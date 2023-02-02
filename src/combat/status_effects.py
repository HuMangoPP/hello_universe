STATUS_EFFECTS = [
    'ability_lock', # when an ability is locked, there is not way to cancel
    'ability_cd', # after an ability is used, the ai cannot use another ability for some time
    'weakened', # reduced power and reduced defense
    'bleeding', # dot and reduce mobility
    'poisoned', # dot and reduced mobility / make same as bleeding?
    'stunned', # reduced mobility
    'intimidated', # causes enemies to run away
    'in_air',
    'underwater'
    'strike',
    'grapple'
]

MOVEMENT_IMPAIR_EFFECTS = [
    'bleeding', 'poisoned', 'weakened',
]

DOT_EFFECTS = [
    'poisoned', 'bleeding',
]

BASE_CD = 1000