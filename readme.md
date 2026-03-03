Vampire the Masquerade: Redemption import/export plugin for noesis
======
original author: Durik256\
update: hypov8

## usefull links
https://web.archive.org/web/20210110082035/https://www.e-mods.net/nodsdk/Docs/NOD.htm
https://web.archive.org/web/20210110082006/https://www.e-mods.net/nodsdk/Docs/NAD.htm
https://www.moddb.com/members/lithtechguru/tutorials/how-to-import-models-from-blender-into-vampire-the-masquerade-redemption
https://www.moddb.com/games/vampire-the-masquerade-redemption/tutorials/how-to-import-models-from-blender-into-vampire-the-masquerade-redemption
https://ide.kaitai.io/


.nad export options
------
- \-nadtpose\
    export animation file in tpose(if thats rest position).\
    used to helps to skin a new mesh to skeleton.
- \-nadtaglist \<arg,arg\>\
    add tags to animation file.(frame,type) eg -nadtaglist 3.0,5,15.0,4
- \-nadnoopt\
    dont reduce keyframe counts. every frame is a keyframe


version 1.0 (2024-04-04)
------
- updated .nad reader
- added .nad exporter
- added popup to choose .nad (for mesh imported with bones)
- fixed import fps
- added export options -nadtaglist -nadtpose


version 1.1 (2024-04-08)
------
- added linear key reduction (use -nadnoopt to disable)
- fixed import frame count issues (range -1)
- fixed export frame count issues (range +1)
