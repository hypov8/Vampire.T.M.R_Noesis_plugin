#by Durik256
from inc_noesis import *
import noesis

def registerNoesisTypes():
    handle = noesis.register("Vampire the Masquerade Redemption", ".NOD")
    noesis.setHandlerTypeCheck(handle, CheckType)
    noesis.setHandlerLoadModel(handle, LoadModel)
    noesis.setHandlerWriteModel(handle, noepyWriteModel)
    noesis.setTypeExportOptions(handle, "-maxvertweights %i -maxverts %i"%(2, 800))
    return 1

def CheckType(data):

    return 1

bones = []
def LoadModel(data, mdlList):
    bs = NoeBitStream(data)
    ctx = rapi.rpgCreateContext()
    global bones
    bones = []
    #Format
    Version = bs.readUInt()
    NumMaterials = bs.readUInt()
    
    materials = []
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
    print(ModelFlags,NumVertices,NumFaces,NumGroups)
    
    #ModelFlags Bitvector Definition
    HASLOD = ModelFlags & 0x1
    INLINE = ModelFlags & 0x2
    STATIC = ModelFlags & 0x4
    RESERVED1 = ModelFlags & 0x8
    RESERVED2 = ModelFlags & 0x10
    
    print("HASLOD:", HASLOD)
    print("INLINE:", INLINE)
    print("STATIC:", STATIC)
    print("RESERVED1:", RESERVED1)
    print("RESERVED2:", RESERVED2)
    
    #Bone Definitions
    
    for x in range(NumBones):#66 bytes
        RestTranslate = NoeVec3.fromBytes(bs.read(12))#bs.read('3f')
        RestMatrixInverse = NoeMat43.fromBytes(bs.read(48)).transpose().inverse()
        SiblingID = bs.readShort()
        ChildID = bs.readShort()
        ParentID = bs.readShort()
        bones.append(NoeBone(x, 'bone_%i'%x, RestMatrixInverse, None, ParentID))
        print(x,'>>>',[ParentID,ChildID,SiblingID])
        print('RestTranslate:',RestTranslate, 'RestMatrixInverse:',RestMatrixInverse)
    
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
        print('>>>>>GROUP:',Material_ID,NumFaces,NumVertices,MinVertices,GroupFlags)
        #---------------
        HASLOD = (GroupFlags & 0x1)#bool
        NOWEIGHTS = (GroupFlags & 0x2)
        NOSKINNING = (GroupFlags & 0x4)
        MULTITEXTURE = (GroupFlags & 0x8)
        print("HASLOD:", HASLOD)
        print("NOWEIGHTS:", NOWEIGHTS)
        print("NOSKINNING:", NOSKINNING)
        print("MULTITEXTURE:", MULTITEXTURE)
        #---------------
        BoneNum = bs.read(1)#bs.readUByte()
        MeshNum = bs.readUByte()
        unk = bs.readUShort()
        print(mesh_names[MeshNum])
        print(Material_ID,NumFaces,NumVertices,MinVertices,GroupFlags,'BoneNum:',BoneNum,MeshNum,unk)
        
        curPos  = bs.tell()
        bs.seek(vbuf_ofs+(vcnt*40))
        vbuf = bs.read(NumVertices * 40)
        wbuf = printWeight(vbuf)
        bs.seek(ibuf_ofs+(icnt*6))
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
    print(vcnt, icnt)

  
    mdl = rapi.rpgConstructModel()##NoeModel()#
    mdl.setBones(bones)
    #mdl.setModelMaterials(NoeModelMaterials(texList, materials))
    mdlList.append(mdl)
    rapi.setPreviewOption("setAngOfs", "0 90 0")
    return 1
    
def printWeight(buf):
    wbuf = b''
    bs = NoeBitStream(buf)
    for x in range(len(buf)//40):
        bs.seek(32,1)
        w0 = bs.read('f4B')
        w1 = [0,0]
        #if w0[1] >= len(bones):
        #    print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>...',w0[1])
        if w0[0] < 0.999999 and bones[w0[1]].parentIndex != -1:
            w1[0] = 1.0 - w0[0]
            w1[1] = bones[w0[1]].parentIndex
        #print(w0[1], w1[1], w0[0], w1[0])
        wbuf += noePack('B', w0[1])
        wbuf += noePack('B', w1[1])
        wbuf += noePack('f', w0[0])
        wbuf += noePack('f', w1[0])

    return wbuf
    
def noepyWriteModel(mdl, bs):
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
        matList.append(NoeBone(0,'Root', NoeMat43()))
    
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
        nodes.append([-1,-1,bone.parentIndex])
        
    #set child
    for x in range(len(nodes)):
        for y in range(len(nodes)):
            if nodes[y][2] == x:
                nodes[x][1] = y
                break
    
    #set sibling
    for x in range(len(nodes)):
        sibling = []
        for y in range(len(nodes)):
            if nodes[x][2] == nodes[y][2]:
                sibling.append(y)
        if sibling:
            for y in range(len(sibling)):
                if sibling[y] == x:
                    if y+1 < len(sibling):
                        nodes[x][0] = sibling[y+1]
        
        
    for i,node in enumerate(nodes):
        print(i,'>>>',[node[2],node[1],node[0]])
    
    local = noeCalculateLocalBoneTransforms(bones)
    #Bone Definitions
    for i,bone in enumerate(bones):#66 bytes
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
            mesh.weights = [NoeVertWeight([0],[1])]*vnum
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
    for j,mesh in enumerate(meshes):
        Material_ID = 0
        for i,mat in enumerate(matList):
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
'''
0 >>> [-1, 1, -1]
1 >>> [0, 2, 5]
2 >>> [1, 3, -1]
3 >>> [2, 4, -1]
4 >>> [3, -1, -1]
5 >>> [0, 6, 9]
6 >>> [5, 7, -1]
7 >>> [6, 8, -1]
8 >>> [7, -1, -1]
9 >>> [0, 10, 12]
10 >>> [9, 11, -1]
11 >>> [10, -1, -1]
12 >>> [0, 13, 14]
13 >>> [12, -1, -1]
14 >>> [0, 15, 39]
15 >>> [14, 16, -1]
16 >>> [15, 17, -1]
17 >>> [16, 18, 21]
18 >>> [17, 19, -1]
19 >>> [18, -1, 20]
20 >>> [18, -1, -1]
21 >>> [16, 22, 26]
22 >>> [21, 23, -1]
23 >>> [22, 24, -1]
24 >>> [23, -1, 25]
25 >>> [23, -1, -1]
26 >>> [16, 27, 31]
27 >>> [26, 28, -1]
28 >>> [27, 29, 30]
29 >>> [28, -1, -1]
30 >>> [27, -1, -1]
31 >>> [16, 32, -1]
32 >>> [31, 33, -1]
33 >>> [32, 34, 35]
34 >>> [33, -1, -1]
35 >>> [32, 36, 37]
36 >>> [35, -1, -1]
37 >>> [32, 38, -1]
38 >>> [37, -1, -1]
39 >>> [0, -1, -1]
'''