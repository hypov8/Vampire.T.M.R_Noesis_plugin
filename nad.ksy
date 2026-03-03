meta:
  id: nad
  endian: le
  file-extension: nad
seq:
  - id: version
    type: u4
    valid: 3
  - id: num_tracks
    type: u4
  - id: flags
    type: u4
  - id: duration
    type: f4
  - id: tracks
    type: track
    repeat: expr
    repeat-expr: num_tracks
  - id: num_tags
    type: u4
  - id: tags
    type: tag
    repeat: expr
    repeat-expr: num_tags
types:
  track:
    seq:
      - id: num_keys
        type: u4
      - id: bone_index
        type: u4
      - id: type
        type: u4
        enum: track_type
      - id: keys
        type: key
        repeat: expr
        repeat-expr: num_keys
  key:
    seq:
      - id: frame
        type: f4
      - id: scale
        type: f4
      - id: value
        type: vec3
      - id: constant_curve_fitting_factor
        type: vec3
      - id: linear_curve_fitting_factor
        type: vec3
      - id: square_curve_fitting_factor
        type: vec3
  tag:
    seq:
      - id: frame
        type: f4
      - id: type
        type: u4
        enum: key_tag
  vec3:
    seq:
      - id: x
        type: f4
      - id: y
        type: f4
      - id: z
        type: f4
enums:
  track_type:
    0: rotate
    1: translate
    2: scale
  key_tag:
    0: lwalk
    1: rwalk
    2: lrun
    3: rrun
    4: fire
    5: strike
    6: cast
    7: fall
    8: project
    9: flap
    10: suck
    11: idle
    12: idle2
    13: codex1
    14: codex2
    15: codex3
    16: repeat
    17: repeat_to
    18: throwdeath
