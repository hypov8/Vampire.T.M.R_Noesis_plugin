#by Durik256
from inc_noesis import *

def registerNoesisTypes():
    handle = noesis.register("Vampire the Masquerade Redemption", ".NAD")
    noesis.setHandlerTypeCheck(handle, CheckType)
    noesis.setHandlerLoadModel(handle, loadAnim)
    return 1

def CheckType(data):
    return 1

verbose = False
SKEL_PATH = r'C:\Users\vlad_\Desktop\NOD\3D\Models\christof.nod'

def loadAnim(data, mdlList):
    bs = NoeBitStream(data)
    animBones, bones = [], []
    haveSkel = False
    
    # Parsing the header
    version = bs.readUInt()
    if verbose: print('version:', version)
    num_bone_tracks = bs.readUInt()
    if verbose: print('num_bone_tracks:', num_bone_tracks)
    try:
        bones = loadSkel(SKEL_PATH)
        haveSkel = True
    except:
        bones = [NoeBone(x,'b_%i'%x,NoeMat43) for x in range(num_bone_tracks)]
    
    flags = bs.readUInt()
    if verbose: print('flags:', flags)
    duration = bs.readFloat()
    if verbose: print('duration:', duration)

    # Parsing each bone track
    for i in range(num_bone_tracks):
        num_keys = bs.readUInt()
        if verbose: print('num_keys:', num_keys)
        bone_num = bs.readUInt()
        if verbose: print('bone_num:', bone_num)
        track_type = bs.readUInt()
        if track_type == 0: t='rotation'
        if track_type == 1: t='translate'
        if track_type == 2: t='scale'
        
        if verbose: print('track_type:', track_type, t)
        posList = []
        rotList = []
        sclList = []
        # Parsing each keyframe in the bone track
        for j in range(num_keys):
            frame = bs.readFloat()
            if verbose: print('frame:', frame)
            frame_scale = bs.readFloat()
            frame = frame/30
            if verbose: print('frame_scale:', frame_scale)
            value = bs.read(12)
            if track_type == 0: 
                value = NoeAngles.fromBytes(value)
                rotList.append(NoeKeyFramedValue(frame, value))
            if track_type == 1: 
                value = NoeVec3.fromBytes(value)
                posList.append(NoeKeyFramedValue(frame, value))
            if track_type == 2: 
                value = NoeVec3.fromBytes(value)
                sclList.append(NoeKeyFramedValue(frame, value))
            if verbose: print('value:', value)
            c_factor = NoeVec3.fromBytes(bs.read(12))
            if verbose: print('c_factor:', c_factor)
            b_factor = NoeVec3.fromBytes(bs.read(12))
            if verbose: print('b_factor:', b_factor)
            a_factor = NoeVec3.fromBytes(bs.read(12))
            if verbose: print('a_factor:', a_factor)
        #---------
        keyBone = NoeKeyFramedBone(bone_num)
        keyBone.setRotation(rotList, noesis.NOEKF_ROTATION_EULER_XYZ_3)
        keyBone.setTranslation(posList)
        keyBone.setScale(sclList, noesis.NOEKF_SCALE_VECTOR_3)
        animBones.append(keyBone)
        #---------

    # Parsing the keyframe tags
    num_tags = bs.readUInt()
    if verbose: print('num_tags:', num_tags)

    for i in range(num_tags):
        frame_num = bs.readFloat()
        if verbose: print('frame_num:', frame_num)
        tag_type = bs.readUInt()
        if verbose: print('tag_type:', tag_type)

    anim = NoeKeyFramedAnim('anim_0', bones, animBones, 30)
    mdl = NoeModel()
    mdl.setAnims([anim])
    mdl.setBones(bones)
    mdlList.append(mdl)
    rapi.setPreviewOption("setAngOfs", "0 90 0")
    return 1

def loadSkel(path):
    bs = NoeBitStream(rapi.loadIntoByteArray(path))
    bones = []

    v = bs.readUInt()
    nm = bs.readUInt()
    bs.seek(32*nm,1)
    nb = bs.readUShort()
    bs.seek(40,1)
    for x in range(nb):
        bs.seek(12,1)
        mat43 = NoeMat43.fromBytes(bs.read(48)).transpose().inverse()
        bs.seek(4,1)
        parent = bs.readShort()
        bones.append(NoeBone(x, 'bone_%i'%x, mat43, None, parent))
    return bones