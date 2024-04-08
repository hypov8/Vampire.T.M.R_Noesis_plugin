'''
update: hypov8

original author: Durik256

'''

from inc_noesis import *

DEBUG_PRINT = False
NOD_VERSION = 7

# pylint: disable=multiple-statements, fixme, invalid-name
#   locally-disabled,line-too-long


def registerNoesisTypes():
    ''' noesis plugin config '''
    handle = noesis.register("Vampire: TMR (NOD Mesh)", ".nod")
    noesis.setHandlerTypeCheck(handle, nod_checkType)
    noesis.setHandlerLoadModel(handle, nod_loadModel)
    noesis.setHandlerWriteModel(handle, nod_write_model)
    noesis.setTypeExportOptions(handle, "-maxvertweights %i -maxverts %i"%(2, 800))
    return 1


def nod_checkType(data):
    ''' run simple check on file '''
    bs = NoeBitStream(data)
    Version = bs.readUInt()
    if Version != NOD_VERSION:
        print('ERROR: Wrong version (%i). expecting (%i)'% (Version, NOD_VERSION))
    return 1


# bones = []

def nod_loadModel(data, mdlList):
    ''' '''

    def nod_printWeight(buf, bones):
        wbuf = b''
        bs = NoeBitStream(buf)
        for _ in range(len(buf)//40):
            bs.seek(32, 1)
            w0 = bs.read('f4B')
            w1 = [0, 0]
            if w0[0] < 0.999999 and bones[w0[1]].parentIndex != -1:
                w1[0] = 1.0 - w0[0]
                w1[1] = bones[w0[1]].parentIndex
            wbuf += noePack('B', w0[1])
            wbuf += noePack('B', w1[1])
            wbuf += noePack('f', w0[0])
            wbuf += noePack('f', w1[0])
        return wbuf
    # END nod_printWeight

    def nod_load_external_nad_file(mdl, bones):
        ''' file has bones. ask to import .nad '''

        def validate_nod_file(filename):
            print('filename: ', filename)
            if (filename is None) or (filename == ''):
                return "Error: empty file path"
            if not rapi.checkFileExists(filename):
                return "Error: invalid file path"
            if filename[len(filename) -4:] != '.nad':
                return "Error: invalid file extension"
            print('filename ok')
            return None

        if DEBUG_PRINT:
            noesis.logPopup()
        print("====== mesh has bones ==========")

        nad_file = noesis.userPrompt( \
            noesis.NOEUSERVAL_FILEPATH,
            'Import Animation', # title string
            'Found bones. Select a .nad animtion file to use...', # prompt string
            '', # default value string
            validate_nod_file)  # input validation handler

        if nad_file:
            # getExtensionlessName
            try:
                print('Animation file: ' + nad_file)
                from fmt_NAD import nad_import_merge_anims_to_mesh
                _, _, kfAnims = nad_import_merge_anims_to_mesh(nad_file, bones)
                mdl.setAnims(kfAnims)
            except Exception as e:
                print('failed to load anims: ', e)
    # END nod_printWeight

    print("====== start import NOD ======")

    bs = NoeBitStream(data)
    ctx = rapi.rpgCreateContext()
    # global bones
    bones = []
    materials = []

    #Format
    Version = bs.readUInt()
    if Version != NOD_VERSION:
        print('ERROR: Wrong version (%i). expecting (%i)'% (Version, NOD_VERSION))

    NumMaterials = bs.readUInt()
    for x in range(NumMaterials):
        name = noeStrFromBytes(bs.read(32))
        materials.append(NoeMaterial(name, ''))

    NumBones = bs.readUShort()
    NumMeshs = bs.readUShort()
    NumVertices = bs.readUInt()
    NumFaces = bs.readUInt()
    NumGroups = bs.readUShort()
    ModelFlags = bs.readUInt()
    Bounds = bs.read('6f')#min(XYZ), max(XYZ)
    print(
        'flags:%i '%(ModelFlags),
        'verts:%i '%(NumVertices),
        'faces:%i '%(NumFaces),
        'groups:%i '%(NumGroups),
        'materials:%i '%(NumMaterials))

    #ModelFlags Bitvector Definition
    HASLOD = ModelFlags & 0x1
    INLINE = ModelFlags & 0x2
    STATIC = ModelFlags & 0x4
    RESERVED1 = ModelFlags & 0x8
    RESERVED2 = ModelFlags & 0x10

    print(
        "HasLOD:%i "%(HASLOD),
        "Inline:%i "%(INLINE),
        "Static:%i "%(STATIC),
        "Reserved1:%i "%(RESERVED1),
        "Reserved2:%i "%(RESERVED2))

    #Bone Definitions
    if DEBUG_PRINT:
        print("%-6s %3s %3s %3s"% ('bone# ', 'P', 'Ch', 'Si'))
    for x in range(NumBones):#66 bytes
        RestTranslate = NoeVec3.fromBytes(bs.read(12))#bs.read('3f')
        RestMatrixInverse = NoeMat43.fromBytes(bs.read(48)).transpose().inverse()
        SiblingID = bs.readShort()
        ChildID = bs.readShort()
        ParentID = bs.readShort()
        bones.append(NoeBone(x, 'bone_%i'%x, RestMatrixInverse, None, ParentID))
        if DEBUG_PRINT:
            print("%-3i%3s[%3i,%3i,%3i]"% (x, '>>>', ParentID, ChildID, SiblingID))
            print('RestTranslate:', RestTranslate, 'RestMatrixInverse:', RestMatrixInverse)

    mesh_names = []
    for x in range(NumMeshs):
        name = noeStrFromBytes(bs.read(32))
        mesh_names.append(name)

    vbuf_ofs = bs.tell()
    bs.seek(NumVertices * 40, 1)

    if HASLOD:
        bs.seek(NumVertices * 2, 1)

    ibuf_ofs = bs.tell()
    bs.seek(NumFaces * 6, 1)

    vcnt, icnt = 0, 0
    for x in range(NumGroups):#
        Material_ID = bs.readInt()
        RESERVED = bs.read(12)#This field should be ignored
        NumFaces = bs.readUShort()
        NumVertices = bs.readUShort()
        MinVertices = bs.readUShort()
        GroupFlags = bs.readUShort()
        if DEBUG_PRINT:
            print('>>>>>GROUP:', Material_ID, NumFaces, NumVertices, MinVertices, GroupFlags)
        #---------------
        HASLOD = (GroupFlags & 0x1)#bool
        NOWEIGHTS = (GroupFlags & 0x2)
        NOSKINNING = (GroupFlags & 0x4)
        MULTITEXTURE = (GroupFlags & 0x8)
        if DEBUG_PRINT:
            print("HASLOD:", HASLOD)
            print("NOWEIGHTS:", NOWEIGHTS)
            print("NOSKINNING:", NOSKINNING)
            print("MULTITEXTURE:", MULTITEXTURE)
        #---------------
        BoneNum = bs.read(1)#bs.readUByte()
        MeshNum = bs.readUByte()
        unk = bs.readUShort()
        if DEBUG_PRINT:
            print(mesh_names[MeshNum])
            print(Material_ID, NumFaces, NumVertices, MinVertices, GroupFlags, 'BoneNum:', BoneNum, MeshNum, unk)

        curPos = bs.tell()
        bs.seek(vbuf_ofs+(vcnt*40))
        vbuf = bs.read(NumVertices * 40)
        wbuf = nod_printWeight(vbuf, bones)
        bs.seek(ibuf_ofs+(icnt*6))
        if DEBUG_PRINT:
            print('ifs:',bs.tell())
        ibuf = bs.read(NumFaces * 6)

        vcnt += NumVertices
        icnt += NumFaces

        rapi.rpgSetName(mesh_names[MeshNum])
        rapi.rpgSetMaterial(materials[Material_ID].name)
        rapi.rpgBindPositionBuffer(vbuf, noesis.RPGEODATA_FLOAT, 40)
        rapi.rpgBindNormalBufferOfs(vbuf, noesis.RPGEODATA_FLOAT, 40, 12)
        rapi.rpgBindUV1BufferOfs(vbuf, noesis.RPGEODATA_FLOAT, 40, 24)

        if not NOSKINNING:
            rapi.rpgBindBoneIndexBuffer(BoneNum*NumVertices, noesis.RPGEODATA_UBYTE, 1, 1)
            rapi.rpgBindBoneWeightBuffer(b'\xFF'*NumVertices, noesis.RPGEODATA_UBYTE, 1, 1)
        else:
            #rapi.rpgBindBoneIndexBufferOfs(vbuf, noesis.RPGEODATA_UBYTE, 40, 36, 1)
            #rapi.rpgBindBoneWeightBufferOfs(vbuf, noesis.RPGEODATA_FLOAT, 40, 32, 1)
            rapi.rpgBindBoneIndexBuffer(wbuf, noesis.RPGEODATA_UBYTE, 10, 1)
            rapi.rpgBindBoneWeightBufferOfs(wbuf, noesis.RPGEODATA_FLOAT, 10, 2, 1)
        rapi.rpgCommitTriangles(ibuf, noesis.RPGEODATA_SHORT, len(ibuf)//2, noesis.RPGEO_TRIANGLE)
        rapi.rpgClearBufferBinds()
        bs.seek(curPos)
    print('verts:%i faces:%i'%(vcnt, icnt))

    mdl = rapi.rpgConstructModel()##NoeModel()#


    # ################################## #
    # load animations from seperate file #
    if NumBones:
        nod_load_external_nad_file(mdl, bones)

    #mdl.setModelMaterials(NoeModelMaterials(texList, materials))
    mdl.setBones(bones)
    mdlList.append(mdl)
    rapi.setPreviewOption("setAngOfs", "0 90 0")
    print("====== finished reading NOD ======")
    return 1


def nod_write_model(mdl, bs: NoeBitStream):
    ''' _ '''
    print('WRITE NOD')
    #Format
    bs.writeUInt(7)#version

    matList = mdl.modelMats.matList
    if not matList:
        matList.append(NoeMaterial('default', ''))

    bs.writeUInt(len(matList))#тumMaterials

    for mat in matList:
        name = mat.name[:32]
        bs.writeBytes(name.encode() + (b'\x00'*(32-len(name))))

    bones = mdl.bones
    if not matList:
        matList.append(NoeBone(0, 'Root', NoeMat43()))

    meshes = mdl.meshes
    min_bounds, max_bounds = NoeVec3(), NoeVec3()
    total_vert, total_tris = 0, 0

    for mesh in meshes:
        total_vert += len(mesh.positions)
        total_tris += len(mesh.indices)//3

        for pos in mesh.positions:
            min_bounds = NoeVec3([min(pos[0], min_bounds[0]), min(pos[1], min_bounds[1]), min(pos[2], min_bounds[2])])
            max_bounds = NoeVec3([max(pos[0], max_bounds[0]), max(pos[1], max_bounds[1]), max(pos[2], max_bounds[2])])

    bs.writeUShort(len(bones))#numBones
    bs.writeUShort(len(meshes))#numMeshs
    bs.writeUInt(total_vert)#numVertices
    bs.writeUInt(total_tris)#numFaces
    bs.writeUShort(len(meshes))#numGroups
    bs.writeUInt(0)#ModelFlags

    bs.writeBytes(min_bounds.toBytes())
    bs.writeBytes(max_bounds.toBytes())

    nodes = []#SiblingID, ChildID, ParentID
    #create nodes info
    for bone in bones:
        nodes.append([-1, -1, bone.parentIndex])

    len_nodes = len(nodes)

    #set child
    for x in range(len_nodes):
        for y in range(len_nodes):
            if nodes[y][2] == x:
                nodes[x][1] = y
                break

    #set sibling
    for x in range(len_nodes):
        sibling = []
        for y in range(len_nodes):
            if nodes[x][2] == nodes[y][2]:
                sibling.append(y)
        if sibling:
            len_sibling = len(sibling)
            for y in range(len_sibling):
                if sibling[y] == x:
                    if y+1 < len_sibling:
                        nodes[x][0] = sibling[y+1]

    if DEBUG_PRINT:
        print("%-6s %3s %3s %3s"% ('bone# ', 'P', 'Ch', 'Si'))
        for i, node in enumerate(nodes):
            # print(i, '>>>', [node[2], node[1], node[0]])
            print("%-3i%3s[%3i,%3i,%3i]"% (i, '>>>', node[2], node[1], node[0]))
            # )
    # local = noeCalculateLocalBoneTransforms(bones)
    #Bone Definitions
    for i, bone in enumerate(bones):#66 bytes
        if bone.parentIndex != -1:
            restTranslate = (bone.getMatrix() * bones[bone.parentIndex].getMatrix().inverse())[3]
        else:
            restTranslate = bone.getMatrix()[3]
        #restTranslate = local[i].inverse()[3]

        bs.writeBytes(restTranslate.toBytes())#restTranslate
        bs.writeBytes(bone.getMatrix().inverse().transpose().toBytes())#restMatrixInverse
        bs.writeShort(nodes[i][0])#SiblingID
        bs.writeShort(nodes[i][1])#ChildID
        bs.writeShort(bone.parentIndex)#ParentID

    #write meshes names
    for mesh in meshes:
        name = mesh.name[:32]
        bs.writeBytes(name.encode() + (b'\x00'*(32-len(name))))

    #write all verts
    for mesh in meshes:
        vnum = len(mesh.positions)
        if len(mesh.normals) <= 0:
            mesh.normals = [NoeVec3()]*vnum
        if len(mesh.uvs) <= 0:
            mesh.uvs = [NoeVec3()]*vnum
        if len(mesh.weights) <= 0:
            mesh.weights = [NoeVertWeight([0], [1])]*vnum
        #mesh.weights = [NoeVertWeight([0],[1])]*vnum
        for x in range(vnum):
            bs.writeBytes(mesh.positions[x].toBytes())
            bs.writeBytes(mesh.normals[x].toBytes())
            bs.writeFloat(mesh.uvs[x][0]);bs.writeFloat(mesh.uvs[x][1])
            bs.writeFloat(mesh.weights[x].weights[0])
            bs.writeByte(mesh.weights[x].indices[0])
            bs.writeBytes(b'\x00\x00\x00')

    #write all indices
    for mesh in meshes:
        for x in mesh.indices:
            bs.writeUShort(x)

    #write mesh group
    for j, mesh in enumerate(meshes):
        Material_ID = 0
        for i, mat in enumerate(matList):
            if mesh.matName == mat.name:
                Material_ID = i

        bs.writeInt(Material_ID)#material_ID
        bs.writeBytes(b'\x00'*12)#RESERVED This field should be ignored
        bs.writeUShort(len(mesh.indices)//3)#numFaces
        bs.writeUShort(len(mesh.positions))#numVertices
        bs.writeUShort(52685)#minVertices
        bs.writeUShort(52687)#groupFlags
        bs.writeUByte(0)#boneNum
        bs.writeUByte(j)#meshNum
        bs.writeUShort(0)#unk
    return 1
    #95.507 17.845 -3.004
    #0.868 -29.758 -0.031
