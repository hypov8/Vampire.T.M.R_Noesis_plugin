'''
original author: Durik256


update: hypov8


version 1.0 (2024-04-04)
===========
updated .nad reader
added .nad exporter
added popup to choose .nad (for mesh imported with bones)
fixed import fps
added export options -nadtaglist -nadtpose


options
========
-nadtpose
    export animation file in tpose(if thats rest position).
    used to helps to skin a new mesh to skeleton
-nadtaglist <arg>
    add tags to animation file.(frame,type) eg -nadtaglist 3.0,5,15.0,4

tag type:
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


default noesis switch's
========
-bonemap <file> - specifies a .bma file to lay out a complete skeleton.
-loadanim <file> - loads animation from a file, to export with main data.
-noanims - skip all animation writes/exports.
-nogeo - skip all geometry writes/exports.


todo
========
click .nad with model open applies animation? if posible!!
check if bone count match mesh?
key reduction
fix animation import names. match original filename..
set an export framerate(fixed at 0.1)
-looping? last keyframe (0x0000807f)
'''


from inc_noesis import * # noesis, NoeVec3, NoeBone, NoeAnim, NoeBitStream

# pylint: disable=multiple-statements, fixme, invalid-name
#   locally-disabled,line-too-long

NAD_VERSION = 3
NAD_FRAMERATE = 30
NAD_OPT_TPOSE = "-nadtpose"
NAD_OPT_TAGLIST = "-nadtaglist"


def registerNoesisTypes():
    ''' _ '''
    # importer NAD
    handle = noesis.register("Vampire: TMR (NAD import)", ".nad")
    noesis.setHandlerTypeCheck(handle, nad_import_check_type)
    noesis.setHandlerLoadModel(handle, nad_import_load_anim)
    # hypov8 export NAD
    handle = noesis.register("Vampire: TMR (NAD export)", ".nad")
    noesis.setHandlerWriteAnim(handle, nad_export_anim)
    noesis.addOption(handle, NAD_OPT_TPOSE, "export animation in t-pose.", 0)
    noesis.addOption(handle, NAD_OPT_TAGLIST, "add tags to animation file. <time,type,time,...>", noesis.OPTFLAG_WANTARG)
    return 1

# isTpose = noesis.optWasInvoked(NAD_OPT_TPOSE)
# hasTagList = noesis.optWasInvoked(NAD_OPT_TAGLIST)

#header indexes
HDR_VER = 0
HDR_NUM_TRK = 1
HDR_FLAGS = 2
HDR_NUM_FRAME = 3
HDR_TRACKS = 4
HDR_NUM_TAG = 5
HDR_TAGS = 6

# bone track index
BTRACK_0_NUM_KEYS = 0   # "B_NUM"
BTRACK_1_INDEX = 1      # "B_INDEX"
BTRACK_2_TYPE = 2       # "B_TYPE"
BTRACK_3_KEYS = 3       # "B_KEYS"

#key indexes
KF_0_FR = 0
KF_1_SCALE = 1
KF_2_XYZ = 2
KF_3_CFACT = 3
KF_4_BFACT = 4
KF_5_AFACT = 5

# key types
TRK_TYPE_0_ROT = 0
TRK_TYPE_1_POS = 1
TRK_TYPE_2_SCL = 2
TRACK_TYPES = ['rotation', 'translate', 'scale']

BONE_ANIMS_IDX = 0
BONE_ANIMS_T = 1
BONE_ANIMS_R = 2

verbose = False # True


class nad_key_rot:
    ''' nad key data'''
    def __init__(self, frame: float, scale: float, xyz: NoeAngles, const_cf: NoeVec3, linear_cf: NoeVec3, square_cf: NoeVec3):
        self.frame = frame          # 0
        self.scale = scale          # 1
        self.xyz = xyz              # 2
        self.const_cf = const_cf    # 3
        self.linear_cf = linear_cf  # 4
        self.square_cf = square_cf  # 5


class nad_key_xyz:
    ''' nad key data'''
    def __init__(self, frame: float, scale: float, xyz: NoeVec3, const_cf: NoeVec3, linear_cf: NoeVec3, square_cf: NoeVec3):
        self.frame = frame          # 0
        self.scale = scale          # 1
        self.xyz = xyz              # 2
        self.const_cf = const_cf    # 3
        self.linear_cf = linear_cf  # 4
        self.square_cf = square_cf  # 5


def nad_export_anim(anims: NoeAnim, bs: NoeBitStream):
    ''' entry for animation export '''
    print('WRITE: Vampire the Masquerade Redemption .NAD')

    # inform the user that the format only supports joint model-anim export
    if rapi.isGeometryTarget() == 1:
        print("WARNING: Model only contains a mesh.")
        return 0
    # rapi.setDeferredAnims(anims)

    def key_reduction(array, frameRate):
        # key reduction (rotation)
        # l_ = len(r_)-1
        # for i, r in enumerate(r_):
        #     if i == 0:
        #         r_anims.append(r)
        #     elif i == l_:
        #         r_anims.append(r)
        #         r_prev = r_[i-1]
        #         r_cur = r_[1]
        #         r_next = r_[i+1]

        #         if

        #             r_anims.append(r)

        # if bone.parentIndex != -1:
        #     restTranslate = (bone.getMatrix() * bones[bone.parentIndex].getMatrix().inverse())[3]
        # else:
        #     restTranslate = bone.getMatrix()[3]
        return
    # END key_reduction

    def build_track_data(anim_bone_array, frameRate):
        ''' full bone data in array '''
        count_tracks = 0
        bone_tracks = []
        isTpose = noesis.optWasInvoked(NAD_OPT_TPOSE)
        print('option T-Pose: ', isTpose)

        print("track count: ", len(anim_bone_array))
        for b_idx, fr_bones in enumerate(anim_bone_array): #[b][fr]
            # print("bone: ", b_idx, " len: ", len(fr_bones))
            t_anims, r_anims = [], []
            for fr, bone in enumerate(fr_bones):
                # bone: NoeBone
                mat = bone.getMatrix()
                ang_cur = mat.toAngles()
                # (pitch, roll, yaw)
                rot = NoeAngles((-ang_cur[0], ang_cur[2], ang_cur[1])).normalize180()
                pos = mat.__getitem__(3)

                if isTpose:
                    rot = NoeAngles()
                    pos = NoeVec3((0.0, 0.0, 0.0))
                scale = float(0.0333) # TODO 1/(FPS)
                r_anims.append(
                    nad_key_rot(
                        float(fr),  # KF_0_FR = 0
                        scale,      # KF_1_SCALE = 1 TODO
                        rot,        # KF_2_XYZ = 2
                        NoeVec3(),  # KF_3_CFACT = 3
                        NoeVec3(),  # KF_4_BFACT = 4
                        NoeVec3())) # KF_5_AFACT = 5
                # root bone contains position
                if bone.parentIndex == -1:
                    t_anims.append(
                        nad_key_xyz(
                            float(fr),  # KF_0_FR = 0
                            scale,      # KF_1_SCALE = 1 TODO
                            pos,        # KF_2_XYZ = 2
                            NoeVec3(),  # KF_3_CFACT = 3
                            NoeVec3(),  # KF_4_BFACT = 4
                            NoeVec3())) # KF_5_AFACT = 5
                # if fr == 12:
                #     break

            count_tracks += 1 if (len(t_anims) > 0) else 0
            count_tracks += 1 if (len(r_anims) > 0) else 0

            bone_tracks.append((
                b_idx,    # BONE_ANIMS_IDX = 0
                t_anims,  # BONE_ANIMS_T = 1
                r_anims)) # BONE_ANIMS_R = 2

        return bone_tracks, count_tracks
    # END build_track_data():

    def get_aniated_bone_array(anim, l_bones, l_frames):
        ''' pack bones into frames '''
        anim_bones_array = []
        anim_bones_sorted = []

        # apply animation matrix to bone
        for fr_idx in range(l_frames):
            n_bones = []
            # b: NoeBone
            for b_idx, b in enumerate(anim.bones):
                n_bone = NoeBone(b.index, b.name, b.getMatrix(), b.parentName, b.parentIndex)
                n_bone.setMatrix(anim.frameMats[l_bones * fr_idx + b.index]) #b_idx?
                n_bones.append(n_bone)
            anim_bones_array.append(n_bones)
        print('v2 boneCnt: ', len(anim_bones_array))

        # sort array into [bone_idx][keyframes]
        for b_idx in range(l_bones):
            n_bones = []
            for fr_idx in range(l_frames):
                n_bones.append(anim_bones_array[fr_idx][b_idx])
            anim_bones_sorted.append(n_bones)
        del anim_bones_array

        return anim_bones_sorted
    # END get_aniated_bone_array

    def get_tag_data():
        ''' get tag data from commandline. '''
        tagList = []
        if noesis.optWasInvoked(NAD_OPT_TAGLIST):
            tag_str = noesis.optGetArg(NAD_OPT_TAGLIST)
            print("taglist: ", tag_str)
            tags_array = tag_str.split(",")
            if len(tags_array) >= 2:
                for i in range(0, len(tags_array), 2):
                    tagList.append((tags_array[i], tags_array[i+1]))
        tag_length = len(tagList)
        if tag_length > 0:
            return tagList, tag_length
        return [], 0
    # END get_tag_data

    print('anims...')
    print("anim sequecnes: ", len(anims))
    # annotate type
    # anim: NoeAnim
    # bone: NoeBone

    # ############################### #
    # loop through animation tracks   #
    # exporter only send 1 at a time? #
    model_array = []
    for anim in anims: #anim: NoeAnim
        print('anim....')
        count_tracks = 0
        l_bones = len(anim.bones)
        l_frames = anim.numFrames
        bone_tracks = []

        # pack animated bones [b][fr] #TODO only need matrix
        bones_animated = get_aniated_bone_array(anim, l_bones, l_frames)
        # get animation data
        bone_tracks, count_tracks = build_track_data(bones_animated, anim.frameRate)
        # add tags
        tag_list, tag_count = get_tag_data()

        print("mdl frameRate: ", anim.frameRate)
        print("mdl numFrames: ", anim.numFrames)
        print("nad trackCount: ", count_tracks)
        print("nad boneCount: ", len(bone_tracks))
        print("nad tagCount: ", tag_count)

        # len_anims = len(bone_tracks)
        model_array.append(( \
            NAD_VERSION,     # 0 HDR_VER
            count_tracks,    # 1 HDR_NUM_TRK
            0,               # 2 HDR_FLAGS
            anim.numFrames,  # 3 HDR_NUM_FRAME
            bone_tracks,     # 4 HDR_TRACKS
            tag_count,       # 5 HDR_NUM_TAG
            tag_list,        # 6 HDR_TAGS
            anim.frameRate)) # TODO..

        break # 1 track only

    # output file. TODO test: handel multiple anim sequences?
    print('write to file')
    for mdl in model_array:
        nad_write_file(bs, mdl)
        # TODO error checking
    return 1


def nad_write_file(bs: NoeBitStream, m_data):
    ''' write data to .nad file'''
    def write_key(bs: NoeBitStream, key_data: nad_key_xyz):
        ''' write key '''
        # print('write key...')
        bs.writeFloat(key_data.frame)               # 0 frame
        bs.writeFloat(key_data.scale)               # 1 scale
        bs.writeBytes(key_data.xyz.toBytes())       # 2 value
        bs.writeBytes(key_data.const_cf.toBytes())  # 3 constant_curve_fitting_factor
        bs.writeBytes(key_data.linear_cf.toBytes()) # 4 linear_curve_fitting_factor
        bs.writeBytes(key_data.square_cf.toBytes()) # 5 square_curve_fitting_factor

    def write_keys(bs: NoeBitStream, bone_data):
        ''' loop through all keys attached to bone rot/pos'''
        for dat in bone_data:
            write_key(bs, dat)

    def nad_write_track(bs: NoeBitStream, bones):
        ''' write bone tracks '''
        for bone in bones:
            b_idx = bone[BONE_ANIMS_IDX]
            len_r = len(bone[BONE_ANIMS_R])
            len_t = len(bone[BONE_ANIMS_T])
            # print("boneIdx: %i r: %i t: %i"% (b_idx, len_r, len_t))
            if len_r > 0:
                bs.writeUInt(len_r)                # 0 num_keys
                bs.writeUInt(b_idx)                # 1 bone_index
                bs.writeUInt(TRK_TYPE_0_ROT)       # 2 track_type
                write_keys(bs, bone[BONE_ANIMS_R]) # 3 keys[]

            if len_t > 0:
                bs.writeUInt(len_t)                # 0 num_keys
                bs.writeUInt(b_idx)                # 1 bone_index
                bs.writeUInt(TRK_TYPE_1_POS)       # 2 track_type
                write_keys(bs, bone[BONE_ANIMS_T]) # 3 keys[]

    def nad_write_tags(bs: NoeBitStream, m_data):
        # hasTagList = noesis.optWasInvoked(NAD_OPT_TAGLIST)
        if len(m_data) > 0:
            for tag in m_data:
                bs.writeFloat(float(tag[0])) # frame time
                bs.writeUInt(int(tag[1])) # tag type
        else:
             bs.writeUInt(0) # empty

    # write file #
    bs.writeUInt(m_data[HDR_VER])           # 0 version
    bs.writeUInt(m_data[HDR_NUM_TRK])       # 1 num_tracks
    bs.writeUInt(m_data[HDR_FLAGS])         # 2 Flags
    bs.writeFloat(m_data[HDR_NUM_FRAME])    # 3 duration (frames/time)
    nad_write_track(bs, m_data[HDR_TRACKS]) # 4 tracks[]
    bs.writeUInt(m_data[HDR_NUM_TAG])       # 5 num_tags
    nad_write_tags(bs, m_data[HDR_TAGS])    # 6 tags
    # return 1/0... TODO error..


def nad_import_check_type(data):
    '''  check version etc '''
    if len(data) < 4:
        return 0
    bs = NoeBitStream(data)
    version = bs.readUInt() # 0 VERSION
    if version != NAD_VERSION:
        print('wrong version')
        return 0
    return 1


# @external. called when loading mesh
def nad_merge_anims_to_mesh(filepath, bones):
    ''' mesh loaded. prompt use for anim path '''
    print('===== merge_nad_anims_to_mesh =====')
    if verbose:
        noesis.logPopup()
        # noesis.logFlush()

    bstream = NoeBitStream(rapi.loadIntoByteArray(filepath))
    #read stream
    track_arrays, bone_count = nad_import_read_stream(bstream)
    #build noesis data
    anim_bones, bones, kfAnims = nad_import_build_noesis_animation(bones, track_arrays, bone_count)

    return anim_bones, bones, kfAnims


# .nad file loaded directly
def nad_import_load_anim(data, mdlList):
    ''' call animation file directly
        TODO apply to existing model?
    '''
    print('===== nad_import_load_anim =====')
    bstream = NoeBitStream(data)
    ctx = rapi.rpgCreateContext()
    if verbose:
        noesis.logPopup()
        # noesis.logFlush()

    #read stream
    track_arrays, bone_count = nad_import_read_stream(bstream)
    #build noesis data
    anim_bones, bones, kfAnims = nad_import_build_noesis_animation([], track_arrays, bone_count)
    #check status
    if anim_bones == 0 and bones == 0:
        return 0

    mdl = NoeModel()
    mdl.setAnims(kfAnims)
    mdl.setBones(bones)
    mdlList.append(mdl)
    rapi.setPreviewOption("setAngOfs", "0 90 0")
    return 1


# build noesis data
def nad_import_build_noesis_animation(bones, track_arrays, bone_count):
    ''' return animated bones '''

    if len(track_arrays) == 0:
        print('no track data')
        return 0, 0, 0

    def nad_build_kf_data(track_arrays, bonesList, animBones, kfAnims):
        print('nad_build_kf_data')
        # bone tracks. each track can be pos/rot/scale (type)
        fr_time_scale = 1.0 / NAD_FRAMERATE
        listTS = []
        for trk in track_arrays:
            # count = trk[BTRACK_0_NUM_KEYS]
            b_idx = trk[BTRACK_1_INDEX] # bone index
            t_type = trk[BTRACK_2_TYPE] # track type
            keys = trk[BTRACK_3_KEYS]   # keyframe array
            posList, rotList, sclList = [], [], []
            # pos0 = NoeVec3()# parent position
            for key in keys:
                # loop through keyframes
                f_time = key[KF_0_FR] * fr_time_scale  # / 30
                scale = key[KF_1_SCALE] # frame time scale. TODO
                xyx = key[KF_2_XYZ]     # pos/rot/scale vector
                cf, bf, af = key[KF_3_CFACT], key[KF_4_BFACT], key[KF_5_AFACT] # F type

                if t_type == TRK_TYPE_0_ROT:
                    rotList.append(NoeKeyFramedValue(f_time, NoeAngles.fromBytes(xyx)))
                elif t_type == TRK_TYPE_1_POS:
                    posList.append(NoeKeyFramedValue(f_time, NoeVec3.fromBytes(xyx)))
                elif t_type == TRK_TYPE_2_SCL: # unused...
                    sclList.append(NoeKeyFramedValue(f_time, NoeVec3.fromBytes(xyx)))

                # work out framerate
                if b_idx == 0 and t_type == TRK_TYPE_0_ROT:
                    listTS.append((f_time, scale))

            keyBone = NoeKeyFramedBone(b_idx)
            keyBone.setRotation(rotList, noesis.NOEKF_ROTATION_EULER_XYZ_3)
            keyBone.setTranslation(posList) #, noesis.NOEKF_TRANSLATION_VECTOR_3)
            keyBone.setScale(sclList, noesis.NOEKF_SCALE_VECTOR_3)
            animBones.append(keyBone)

        frameScale = 1.0
        if len(listTS) >= 2:
            tStart = listTS[0][0]
            tEnd = listTS[1][0]
            tSclale = listTS[0][1]
            frameScale = (tEnd - tStart)* tSclale # usualy = 1.0
        print('calculated framerate: ', frameScale*NAD_FRAMERATE)
        rapi.setPreviewOption("setAnimSpeed", str(NAD_FRAMERATE))
        # TODO name same as file?
        kfAnim = NoeKeyFramedAnim('base_anim', bonesList, animBones, frameRate=NAD_FRAMERATE)
        kfAnims.append(kfAnim)
    #END nad_build_kf_data

    if len(bones) > 0:
        bonesList = bones
    else:
        bonesList = [NoeBone(idx, 'bone_%i'%(idx), NoeMat43()) for idx in range(bone_count)]
    animBones = []
    kfAnims = []

    nad_build_kf_data(track_arrays, bonesList, animBones, kfAnims)

    return animBones, bonesList, kfAnims


# read .nad stream
def nad_import_read_stream(bs: NoeBitStream):
    '''
    read nad file stream
    use bones in mesh object if they exist
    TODO check bone counts
    '''
    def load_keyframes(bs: NoeBitStream, key_count, track_type, bone_num):
        ''' _ '''
        data = []

        # debug it
        if verbose:
            print("-----------")
            print("keyframe count: %i" % (key_count))
            print("track_type: %i (%s)" % (track_type, TRACK_TYPES[track_type]))
            print("bone_num: %i" % (bone_num))
            print("-----------")

        for _ in range(key_count):
            frame = bs.readFloat()  # 0 Frame (Timeline position)
            scale = bs.readFloat()  # 1 FrameScale
            xyz = bs.read(12)       # 2 XYZ (Absolute 3D position or euler angle at this keyframe)
            c_factor = NoeVec3.fromBytes(bs.read(12)) # 3  CFactor (The constant curve fitting factor for the Hermite curve interpolation)
            b_factor = NoeVec3.fromBytes(bs.read(12)) # 4  BFactor (The linear curve fitting factor)
            a_factor = NoeVec3.fromBytes(bs.read(12)) # 5  Afactor (The square curve fitting factor)
            data.append((frame, scale, xyz, c_factor, b_factor, a_factor))
        return data
    #END load_keyframes

    def load_track(bs: NoeBitStream):
        ''' Bone Track Definitions '''
        # bs = NoeBitStream(rapi.loadIntoByteArray(path))
        track = []
        num_key = bs.readUInt()     # 0 NumKeys
        bone_num = bs.readUInt()    # 2 BoneNum
        track_type = bs.readUInt()  # 3 TrackType (0 = rotation, 1 = translate, 2 = scale)
        keyframe = load_keyframes(bs, num_key, track_type, bone_num) # 4 keys
        track = (num_key, bone_num, track_type, keyframe)
        return track, bone_num
    #END load_track

    print("====== start import NAD ==========")
    track_arrays = []
    bone_count = 0

    # ################## #
    # Parsing the header #
    version = bs.readUInt()         # 0 VERSION
    num_bone_tracks = bs.readUInt() # 1 NumBoneTracks
    flags = bs.readUInt()           # 2 Flags
    duration = bs.readFloat()       # 3 duration

    # check version
    if version != NAD_VERSION:
        print("ERROR: wrong version")
        return 0, 0

    # print
    if verbose:
        print('version:', version)
        print('num_bone_tracks:', num_bone_tracks)
        print('flags:', flags)
        print('duration:', duration)

    # #################### #
    # get animation tracks #
    for _ in range(num_bone_tracks):
        trk, bone_idx = load_track(bs)
        track_arrays.append(trk)
        bone_count = max(bone_idx, bone_count)

    # ######################### #
    # Parsing the keyframe tags #
    num_tags = bs.readUInt()
    if verbose:
        noesis.logPopup()
        print('num_tags:', num_tags)
    tag_string = ""
    for i in range(num_tags):
        frame_num = bs.readFloat()
        tag_type = bs.readUInt()
        if len(tag_string) > 0:
            tag_string += ","
        tag_string += "%f,%i"%(frame_num, tag_type)
        if verbose:
            print('tag_num:', i)
            print('frame_num:', frame_num)
            print('tag_type:', tag_type)
    if len(tag_string) > 0:
        print("FOUND TAGS! export str: ", tag_string)
    if verbose:
        print("====== finished reading NAD ==========")

    return track_arrays, bone_count
