# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####


bl_info = {
    "name": "SJ Phaser",
    "description": "Calculate a phase animation.",
    "author": "CaptainHansode",
    "version": (1, 1, 1),
    "blender": (2, 80, 0),
    "location":  "View3D > Sidebar > Tool Tab",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "support": "COMMUNITY",
    "category": "Animation"
}
# web:  https://sakaiden.com
# twitter: https://twitter.com/CaptainHansode
# memo:https://wiki.blender.org/wiki/Process/Addons/Guidelines/metainfo


# Reload modules
if "bpy" in locals():
    import importlib
    mod_list = ["sj_phaser"]
    for mod in mod_list:
        if mod in locals():
            importlib.reload(locals()[mod])


import bpy
from . import sj_phaser


class SJPhaserProperties(bpy.types.PropertyGroup):
    r"""カスタムプロパティを定義する"""
    # frame
    start_frame: bpy.props.IntProperty(name="Start Frame", default=0, min=0)
    end_frame: bpy.props.IntProperty(name="End Frame", default=100, min=1)
    # ディレイ
    delay: bpy.props.FloatProperty(name="Delay", default=3, min=1.0, max=10.0)
    # 再帰
    recursion: bpy.props.FloatProperty(
        name="Recursion", default=5.0, min=0.0, max=10.0)
    # 継続性orパワー 振動の強さ
    strength: bpy.props.FloatProperty(
        name="Strength", default=1.0, min=1.0, max=10.0)
    # 閾値 ベクトル比較の際、外積、dot積のゴミ取り
    threshold: bpy.props.FloatProperty(
        name="Threshold",
        default=0.001, min=0.00001, max=0.1, step=0.01, precision=4)
    debug: bpy.props.BoolProperty(name="Debug", default=False)


class SJPhaserCalculate(bpy.types.Operator):
    r"""Gen phase animation"""
    bl_idname = "sj_phaser.calculate"
    bl_label = "Calculate"
    bl_description = "Calculate a phase animation."

    @classmethod
    def poll(cls, context):
        r""""""
        return context.active_object is not None

    def execute(self, context):
        r""""""
        sjps = context.scene.sj_phaser_props
        spsmod = sj_phaser.SJPhaserModule()

        spsmod.sf = sjps.start_frame
        spsmod.ef = sjps.end_frame
        spsmod.debug = sjps.debug

        # delay def=1 to -inf 必ず1以上
        spsmod.delay = sjps.delay
        # 再帰量 def=0 to max1.0
        spsmod.recursion = sjps.recursion / 10.0
        # 振幅の強さ def=1.0 to max2.0 ベクトルの倍率 2倍以上要らない
        spsmod.strength = 1.0 + ((sjps.strength - 1.0) / 10.0)
        spsmod.threshold = sjps.threshold

        if sjps.start_frame >= sjps.end_frame:
            msg = "Make the start frame smaller than the end frame."
            def draw(self, context):
                self.layout.label(text=msg)
            bpy.context.window_manager.popup_menu(draw, title="Info", icon="INFO")
            self.report({'INFO'}, msg)
            # バグっぽく見えるから禁止
            # raise "Make the start frame smaller than the end frame."
            return {'FINISHED'}

        # フレームセット
        bpy.context.scene.frame_set(sjps.start_frame)
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
        obj_trees = spsmod.get_tree_list()  # 実行するオブジェクトを回収する
        spsmod.del_animkey(obj_trees)  # キーフレームを削除する(初期フレームの値をセット)

        obj_trees = spsmod.set_pre_data(obj_trees)  # 必要な初期matrixなど取得する
        spsmod.excute(obj_trees)  # 実行

        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)  # 再描画
        return {'FINISHED'}


class SJPhaserDelAnim(bpy.types.Operator):
    r"""Del Anim"""
    bl_idname = "sj_phaser.del_anim"
    bl_label = "Delete Keyframe"
    bl_description = "Delaete animation key."

    @classmethod
    def poll(cls, context):
        r""""""
        return context.active_object is not None

    def execute(self, context):
        r""""""
        sjps = context.scene.sj_phaser_props
        spsmod = sj_phaser.SJPhaserModule()

        sf = sjps.start_frame
        ef = sjps.end_frame
        spsmod.sf = sf
        spsmod.ef = ef
        spsmod.debug = sjps.debug
        if sf >= ef:
            msg = "Make the start frame smaller than the end frame."
            def draw(self, context):
                self.layout.label(text=msg)
            bpy.context.window_manager.popup_menu(draw, title="Info", icon="INFO")
            self.report({'INFO'}, msg)
            # raise "Make the start frame smaller than the end frame."
            return {'FINISHED'}
        # フレームセット
        bpy.context.scene.frame_set(sf)
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
        # 実行するオブジェクトを回収する
        obj_trees = spsmod.get_tree_list()
        # キーフレームを削除する(初期フレームの値をセット)
        spsmod.del_animkey(obj_trees)
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)  # 再描画
        return {'FINISHED'}


class SJPhaserPanel(bpy.types.Panel):
    r"""UI"""
    bl_label = "SJ Phaser"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'  # UIのタイプは
    bl_context = "posemode"  # ポーズモード以外は使えない
    bl_category = "SJT"
    bl_options = {'DEFAULT_CLOSED'}  # デフォルトでは閉じている

    def draw(self, context):
        layout = self.layout
        sjps = context.scene.sj_phaser_props

        layout.label(text="Frame")
        row = layout.row()
        row.prop(sjps, "start_frame")
        row.prop(sjps, "end_frame")

        layout.label(text="Properties")
        row = layout.row(align=True)

        # TODO: Icon Lost
        # row.label(text="", icon="HAIR")
        row.prop(sjps, "delay")

        # TODO: Icon Lost
        # row.label(text="", icon="IPO_ELASTIC")
        row.prop(sjps, "recursion")

        # TODO: Icon Lost
        # row.label(text="", icon="FORCE_VORTEX")
        row.prop(sjps, "strength")

        row = layout.row()
        row.prop(sjps, "threshold")

        layout.label(text="Main")
        row = layout.row()
        row.scale_y = 1.8
        row.operator("sj_phaser.calculate", icon="KEYTYPE_KEYFRAME_VEC")
        row = layout.row()
        row.operator("sj_phaser.del_anim", icon="KEYFRAME")
        row = layout.row()


classes = (
    SJPhaserProperties,
    SJPhaserCalculate,
    SJPhaserDelAnim,
    SJPhaserPanel
    )


# Register all operators and panels
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    # プロパティを追加する
    bpy.types.Scene.sj_phaser_props = bpy.props.PointerProperty(type=SJPhaserProperties)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    # プロパティを削除
    del bpy.types.Scene.sj_phaser_props


if __name__ == "__main__":
    register()
