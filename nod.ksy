meta:
  id: nod
  endian: le
  file-extension: nod
seq:
  - id: version
    type: u4
    valid: 7
  - id: num_materials
    type: u4
  - id: material_names
    type: strz
    encoding: ascii
    size: 32
    repeat: expr
    repeat-expr: num_materials
  - id: num_bones
    type: u2
  - id: num_meshes
    type: u2
  - id: num_vertices
    type: u4
  - id: num_faces
    type: u4
  - id: num_groups
    type: u2
  - id: flags
    type: model_flags
  - id: bounds
    type: bounds
  - id: bones
    type: bone
    repeat: expr
    repeat-expr: num_bones
  - id: mesh_names
    type: strz
    encoding: ascii
    size: 32
    repeat: expr
    repeat-expr: num_meshes
  - id: vertices
    type: vertex
    repeat: expr
    repeat-expr: num_vertices
  - id: lod_info
    type: u2
    if: flags.has_lod
    repeat: expr
    repeat-expr: num_vertices
  - id: faces
    type: u2
    repeat: expr
    repeat-expr: num_faces * 3
  - id: groups
    type: group
    repeat: expr
    repeat-expr: num_groups
types:
  group:
    seq:
      - id: material_index
        type: s4
      - id: reserved
        size: 12
      - id: num_faces
        type: u2
      - id: num_vertices
        type: u2
      - id: min_vertices
        type: u2
      - id: flags
        type: group_flags
      - id: bone_index
        type: u1
      - id: mesh_index
        type: u1
      - id: padding
        size: 2
    instances:
      name:
        value: _root.mesh_names[mesh_index]
      material:
        if: material_index != -1
        value: _root.material_names[material_index]
      bone_override:
        if: flags.no_skinning
        value: _root.bones[bone_index]
  bone:
    seq:
      - id: pos
        type: vec3
      - id: inv_matrix
        type: mat34
      - id: sibling_index
        type: s2
      - id: child_index
        type: s2
      - id: parent_index
        type: s2
  vertex:
    seq:
      - id: pos
        type: vec3
      - id: normal
        type: vec3
      - id: uv
        type: vec2
      - id: weight
        type: f4
      - id: bone_index
        type: u1
      - id: padding
        size: 3
    instances:
      bone1:
        value: _root.bones[bone_index]
      bone2:
        if: weight < 1
        value: _root.bones[bone1.parent_index]
  group_flags:
    seq:
      - id: value
        type: u2
    instances:
      has_lod:
        value: (value & 1) != 0
      no_weights:
        value: (value & 2) != 0
      no_skinning:
        value: (value & 4) != 0
      multitexture:
        value: (value & 8) != 0
  model_flags:
    seq:
      - id: value
        type: u4
    instances:
      has_lod:
        value: (value & 1) != 0
      inline:
        value: (value & 2) != 0
      static:
        value: (value & 4) != 0
  vec2:
    seq:
      - id: x
        type: f4
      - id: y
        type: f4
  vec3:
    seq:
      - id: x
        type: f4
      - id: y
        type: f4
      - id: z
        type: f4
  bounds:
    seq:
      - id: min
        type: vec3
      - id: max
        type: vec3
  mat34:
    seq:
      - id: m00
        type: f4
      - id: m10
        type: f4
      - id: m20
        type: f4
      - id: m30
        type: f4
      - id: m01
        type: f4
      - id: m11
        type: f4
      - id: m21
        type: f4
      - id: m31
        type: f4
      - id: m02
        type: f4
      - id: m12
        type: f4
      - id: m22
        type: f4
      - id: m32
        type: f4
