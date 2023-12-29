from pathlib import Path
import vtk

def main():
    colors = vtk.vtkNamedColors()

    fn_1= r'./head-neck-2016-09/grayscale/Osirix-Manix-255-res.nrrd'
    fn_2= r'./head-neck-2016-09/labels/HN-Atlas-labels.nrrd'

    # SliceOrder class instance to manage image orientation.
    so = SliceOrder()
    
    # Create RenderWindow and Renderers for axial, sagittal, and coronal views.
    ren1 = vtk.vtkRenderer() #axial
    ren2 = vtk.vtkRenderer() #sagittal
    ren3 = vtk.vtkRenderer() #coronal
    ren_win = vtk.vtkRenderWindow()
    ren_win.AddRenderer(ren1)
    ren_win.AddRenderer(ren2)
    ren_win.AddRenderer(ren3)
    ren_win.SetWindowName('Neck Slices - Axial, Sagittal, Coronal')

    # Create a RenderWindowInteractor to enable user interaction.
    iren = vtk.vtkRenderWindowInteractor()
    iren.SetRenderWindow(ren_win)

    # Read the grayscale data.
    grey_reader = vtk.vtkNrrdReader()
    grey_reader.SetFileName(str(fn_1))
    grey_reader.Update()
    
    # Set up a lookup table for window and level adjustment.
    wllut = vtk.vtkWindowLevelLookupTable()
    wllut.SetWindow(255)
    wllut.SetLevel(128)
    wllut.SetTableRange(-980,5144)
    wllut.Build()
    
    #AXIAL
    
    aslice_number=int(input("Input slice number from 0 to 206 for axial plane: "))
    
    # Pad the grayscale data to the desired slice number.
    agrey_padder = vtk.vtkImageConstantPad()
    agrey_padder.SetInputConnection(grey_reader.GetOutputPort())
    agrey_padder.SetOutputWholeExtent(0, 255, 0, 255, aslice_number, aslice_number)
    agrey_padder.SetConstant(0)

    # Create the plane source for axial view.
    agrey_plane = vtk.vtkPlaneSource()

    # Apply transformation to the axial plane.
    agrey_transform = vtk.vtkTransformPolyDataFilter()
    agrey_transform.SetTransform(so.get('hfsi'))
    agrey_transform.SetInputConnection(agrey_plane.GetOutputPort())

    # Compute normals for the axial plane.
    agrey_normals = vtk.vtkPolyDataNormals()
    agrey_normals.SetInputConnection(agrey_transform.GetOutputPort())
    agrey_normals.FlipNormalsOff()

    # Mapper for the axial plane.
    agrey_mapper = vtk.vtkPolyDataMapper()
    agrey_mapper.SetInputConnection(agrey_plane.GetOutputPort())

    # Texture mapping for the axial plane.
    agrey_texture = vtk.vtkTexture()
    agrey_texture.SetInputConnection(agrey_padder.GetOutputPort())
    agrey_texture.SetLookupTable(wllut)
    agrey_texture.SetColorModeToMapScalars()
    agrey_texture.InterpolateOn()

    # Actor for the axial plane.
    agrey_actor = vtk.vtkActor()
    agrey_actor.SetMapper(agrey_mapper)
    agrey_actor.SetTexture(agrey_texture)

    # Read the segmented data.
    segment_reader = vtk.vtkNrrdReader()
    segment_reader.SetFileName(str(fn_2))
    segment_reader.Update()

    # ... (Similar setup for segmented data padding, plane source, transformation,
    # normals, mapper, texture, and actor creation as for grayscale data)
    asegment_padder = vtk.vtkImageConstantPad()
    asegment_padder.SetInputConnection(segment_reader.GetOutputPort())
    asegment_padder.SetOutputWholeExtent(0, 255, 0, 255, aslice_number, aslice_number)
    asegment_padder.SetConstant(0)

    asegment_plane = vtk.vtkPlaneSource()

    asegment_transform = vtk.vtkTransformPolyDataFilter()
    asegment_transform.SetTransform(so.get('hfsi'))
    asegment_transform.SetInputConnection(asegment_plane.GetOutputPort())

    asegment_normals = vtk.vtkPolyDataNormals()
    asegment_normals.SetInputConnection(asegment_transform.GetOutputPort())
    asegment_normals.FlipNormalsOn()

    lut = create_head_lut(colors)

    asegment_mapper = vtk.vtkPolyDataMapper()
    asegment_mapper.SetInputConnection(asegment_plane.GetOutputPort())

    asegment_texture = vtk.vtkTexture()
    asegment_texture.SetInputConnection(asegment_padder.GetOutputPort())
    asegment_texture.SetLookupTable(lut)
    asegment_texture.SetColorModeToMapScalars()
    asegment_texture.InterpolateOff()
    
    asegment_actor = vtk.vtkActor()
    asegment_actor.SetMapper(asegment_mapper)
    asegment_actor.SetTexture(asegment_texture)
    
    asegment_overlay_actor = vtk.vtkActor()
    asegment_overlay_actor.SetMapper(asegment_mapper)
    asegment_overlay_actor.SetTexture(asegment_texture)

    asegment_overlay_actor.GetProperty().SetOpacity(.5)
    
    #SAGITTAL

# Sagittal view setup.
# ... (Similar setup for sagittal view as for axial view, with appropriate changes
# to the slice number and orientation)
    
    sslice_number=int(input("Input slice number from 0 to 255 for sagittal plane: "))

    # Check if sp is 21 and ap is 37, print the special message.
    if aslice_number == 21 and sslice_number == 37:
        print("O Panie, to Ty na mnie spojrzałeś")

    sgrey_padder = vtk.vtkImageConstantPad()
    sgrey_padder.SetInputConnection(grey_reader.GetOutputPort())
    sgrey_padder.SetOutputWholeExtent(sslice_number, sslice_number, 0, 255, 0, 206)
    sgrey_padder.SetConstant(0)

    sgrey_plane = vtk.vtkPlaneSource()

    sgrey_transform = vtk.vtkTransformPolyDataFilter()
    sgrey_transform.SetTransform(so.get('hfsi'))
    sgrey_transform.SetInputConnection(sgrey_plane.GetOutputPort())

    sgrey_normals = vtk.vtkPolyDataNormals()
    sgrey_normals.SetInputConnection(sgrey_transform.GetOutputPort())
    sgrey_normals.FlipNormalsOff()

    sgrey_mapper = vtk.vtkPolyDataMapper()
    sgrey_mapper.SetInputConnection(sgrey_plane.GetOutputPort())

    sgrey_texture = vtk.vtkTexture()
    sgrey_texture.SetInputConnection(sgrey_padder.GetOutputPort())
    sgrey_texture.SetLookupTable(wllut)
    sgrey_texture.SetColorModeToMapScalars()
    sgrey_texture.InterpolateOn()

    sgrey_actor = vtk.vtkActor()
    sgrey_actor.SetMapper(sgrey_mapper)
    sgrey_actor.SetTexture(sgrey_texture)

    ssegment_padder = vtk.vtkImageConstantPad()
    ssegment_padder.SetInputConnection(segment_reader.GetOutputPort())
    ssegment_padder.SetOutputWholeExtent(sslice_number, sslice_number, 0, 255, 0, 206)
    ssegment_padder.SetConstant(0)

    ssegment_plane = vtk.vtkPlaneSource()

    ssegment_transform = vtk.vtkTransformPolyDataFilter()
    ssegment_transform.SetTransform(so.get('hfsi'))
    ssegment_transform.SetInputConnection(ssegment_plane.GetOutputPort())

    ssegment_normals = vtk.vtkPolyDataNormals()
    ssegment_normals.SetInputConnection(ssegment_transform.GetOutputPort())
    ssegment_normals.FlipNormalsOn()

    ssegment_mapper = vtk.vtkPolyDataMapper()
    ssegment_mapper.SetInputConnection(ssegment_plane.GetOutputPort())

    ssegment_texture = vtk.vtkTexture()
    ssegment_texture.SetInputConnection(ssegment_padder.GetOutputPort())
    ssegment_texture.SetLookupTable(lut)
    ssegment_texture.SetColorModeToMapScalars()
    ssegment_texture.InterpolateOff()

    ssegment_overlay_actor = vtk.vtkActor()
    ssegment_overlay_actor.SetMapper(ssegment_mapper)
    ssegment_overlay_actor.SetTexture(ssegment_texture)

    ssegment_overlay_actor.GetProperty().SetOpacity(.5)
    
    #CORONAL

# Coronal view setup.
# ... (Similar setup for coronal view as for axial view, with appropriate changes
# to the slice number and orientation)

    cslice_number=int(input("Input slice from 0 to 255 for coronal plane: "))

    cgrey_padder = vtk.vtkImageConstantPad()
    cgrey_padder.SetInputConnection(grey_reader.GetOutputPort())
    cgrey_padder.SetOutputWholeExtent(0, 255, cslice_number, cslice_number, 0, 206)
    cgrey_padder.SetConstant(0)

    cgrey_plane = vtk.vtkPlaneSource()

    cgrey_transform = vtk.vtkTransformPolyDataFilter()
    cgrey_transform.SetTransform(so.get('hfsi'))
    cgrey_transform.SetInputConnection(cgrey_plane.GetOutputPort())

    cgrey_normals = vtk.vtkPolyDataNormals()
    cgrey_normals.SetInputConnection(cgrey_transform.GetOutputPort())
    cgrey_normals.FlipNormalsOff()

    cgrey_mapper = vtk.vtkPolyDataMapper()
    cgrey_mapper.SetInputConnection(cgrey_plane.GetOutputPort())

    cgrey_texture = vtk.vtkTexture()
    cgrey_texture.SetInputConnection(cgrey_padder.GetOutputPort())
    cgrey_texture.SetLookupTable(wllut)
    cgrey_texture.SetColorModeToMapScalars()
    cgrey_texture.InterpolateOn()
    
    cgrey_actor = vtk.vtkActor()
    cgrey_actor.SetMapper(cgrey_mapper)
    cgrey_actor.SetTexture(cgrey_texture)

    csegment_padder = vtk.vtkImageConstantPad()
    csegment_padder.SetInputConnection(segment_reader.GetOutputPort())
    csegment_padder.SetOutputWholeExtent(0, 255, cslice_number, cslice_number, 0, 206)
    csegment_padder.SetConstant(0)

    csegment_plane = vtk.vtkPlaneSource()

    csegment_transform = vtk.vtkTransformPolyDataFilter()
    csegment_transform.SetTransform(so.get('hfsi'))
    csegment_transform.SetInputConnection(csegment_plane.GetOutputPort())

    csegment_normals = vtk.vtkPolyDataNormals()
    csegment_normals.SetInputConnection(csegment_transform.GetOutputPort())
    csegment_normals.FlipNormalsOn()

    csegment_mapper = vtk.vtkPolyDataMapper()
    csegment_mapper.SetInputConnection(csegment_plane.GetOutputPort())

    csegment_texture = vtk.vtkTexture()
    csegment_texture.SetInputConnection(csegment_padder.GetOutputPort())
    csegment_texture.SetLookupTable(lut)
    csegment_texture.SetColorModeToMapScalars()
    csegment_texture.InterpolateOff()

    csegment_overlay_actor = vtk.vtkActor()
    csegment_overlay_actor.SetMapper(csegment_mapper)
    csegment_overlay_actor.SetTexture(csegment_texture)

    csegment_overlay_actor.GetProperty().SetOpacity(.5)
    
    # Set the background color and viewport for each renderer.
    ren1.SetBackground(0, 0, 0)
    ren1.SetViewport(0, 0.5, 0.5, 1)
    ren_win.SetSize(1024,720)
    ren1.AddActor(agrey_actor)
    ren1.AddActor(asegment_overlay_actor)
    asegment_overlay_actor.SetPosition(0, 0, -0.01)
    
    # Camera setup for axial view.
    cam1 = vtk.vtkCamera()
    cam1.SetViewUp(0, -1, 0)
    cam1.SetPosition(0, 0, -1)
    ren1.SetActiveCamera(cam1)
    ren1.ResetCamera()
    cam1.SetViewUp(0, -1, 0)
    cam1.SetFocalPoint(0.0554068, -0.0596001, 0)
    ren1.ResetCameraClippingRange()

    ren2.SetBackground(0, 0, 0)
    ren2.SetViewport(0.5, 0.5, 1, 1)
    ren2.AddActor(cgrey_actor)
    ren2.AddActor(csegment_overlay_actor)
    csegment_overlay_actor.SetPosition(0, 0, -0.01)

# ... (Similar camera setup for sagittal and coronal views)

    cam2 = vtk.vtkCamera()
    cam2.SetViewUp(0, -1, 0)
    cam2.SetPosition(0, 0, -1)
    ren2.SetActiveCamera(cam2)
    ren2.ResetCamera()
    cam2.SetViewUp(0, -1, 0)
    cam2.SetFocalPoint(0.0554068, -0.0596001, 0)
    ren2.ResetCameraClippingRange()

    ren3.AddActor(sgrey_actor)
    ren3.AddActor(ssegment_overlay_actor)
    ssegment_overlay_actor.SetPosition(0, 0, -0.01)
    
    cam3 = vtk.vtkCamera()
    cam3.SetViewUp(0, -1, 0)
    cam3.SetPosition(0, 0, -1)
    ren3.SetActiveCamera(cam3)
    ren3.ResetCamera()
    cam3.SetViewUp(0, -1, 0)
    cam3.SetFocalPoint(0.0554068, -0.0596001, 0)
    ren3.ResetCameraClippingRange()
    
    # Set the background color for all renderers.
    colors.SetColor("BkgColor", [201, 214, 255, 255])
    ren1.SetBackground(colors.GetColor3d('BkgColor'))
    ren2.SetBackground(colors.GetColor3d('BkgColor'))
    ren3.SetBackground(colors.GetColor3d('BkgColor'))

    # Set the viewport for the coronal renderer.
    ren3.SetViewport(0, 0, 1, 0.5)

    ren_win.Render()
    iren.Start()

# Function to create a lookup table for head tissues.
def create_head_lut(colors):
    lut = vtk.vtkLookupTable()
    lut.SetNumberOfColors(141)
    lut.SetTableRange(0, 140)
    lut.Build()

    lut.SetTableValue(0, colors.GetColor4d('alpha'))            #Background
    lut.SetTableValue(10, colors.GetColor4d('white'))            #Skull
    lut.SetTableValue(9, colors.GetColor4d('tan'))           #Hyoid
    lut.SetTableValue(11, colors.GetColor4d('salmon'))           #Atlas
    lut.SetTableValue(12, colors.GetColor4d('lawngreen'))       #Axis
    lut.SetTableValue(13, colors.GetColor4d('wheat'))    #Cervical3
    lut.SetTableValue(14, colors.GetColor4d('coral'))       #Cervical4
    lut.SetTableValue(25, colors.GetColor4d('mediumturquoise'))  #Mandible
    lut.SetTableValue(26, colors.GetColor4d('hotpink'))          #Right clavicle
    lut.SetTableValue(27, colors.GetColor4d('mistyrose'))       #Left clavicle
    lut.SetTableValue(28, colors.GetColor4d('paleturquoise'))   #Sternum
    lut.SetTableValue(31, colors.GetColor4d('goldenrod'))       #Rib 1
    lut.SetTableValue(32, colors.GetColor4d('maroon'))             #Rib 2
    lut.SetTableValue(33, colors.GetColor4d('deepskyblue'))     #Rib 3
    lut.SetTableValue(34, colors.GetColor4d('indigo'))       #Rib 4
    lut.SetTableValue(35, colors.GetColor4d('gold'))           #Rib 5

    return lut

# SliceOrder class defines transformations for proper orientation of slices.
class SliceOrder:
    """
    These transformations permute image and other geometric data to maintain proper
     orientation regardless of the acquisition order. After applying these transforms with
    vtkTransformFilter, a view up of 0,-1,0 will result in the body part
    facing the viewer.
    NOTE: some transformations have a -1 scale factor for one of the components.
          To ensure proper polygon orientation and normal direction, you must
          apply the vtkPolyDataNormals filter.

    Naming (the nomenclature is medical):
    si - superior to inferior (top to bottom)
    is - inferior to superior (bottom to top)
    ap - anterior to posterior (front to back)
    pa - posterior to anterior (back to front)
    lr - left to right
    rl - right to left
    """

    def __init__(self):
        self.si_mat = vtk.vtkMatrix4x4()
        self.si_mat.Zero()
        self.si_mat.SetElement(0, 0, 1)
        self.si_mat.SetElement(1, 2, 1)
        self.si_mat.SetElement(2, 1, -1)
        self.si_mat.SetElement(3, 3, 1)

        self.is_mat = vtk.vtkMatrix4x4()
        self.is_mat.Zero()
        self.is_mat.SetElement(0, 0, 1)
        self.is_mat.SetElement(1, 2, -1)
        self.is_mat.SetElement(2, 1, -1)
        self.is_mat.SetElement(3, 3, 1)

        self.lr_mat = vtk.vtkMatrix4x4()
        self.lr_mat.Zero()
        self.lr_mat.SetElement(0, 2, -1)
        self.lr_mat.SetElement(1, 1, -1)
        self.lr_mat.SetElement(2, 0, 1)
        self.lr_mat.SetElement(3, 3, 1)

        self.rl_mat = vtk.vtkMatrix4x4()
        self.rl_mat.Zero()
        self.rl_mat.SetElement(0, 2, 1)
        self.rl_mat.SetElement(1, 1, -1)
        self.rl_mat.SetElement(2, 0, 1)
        self.rl_mat.SetElement(3, 3, 1)

        """
        The previous transforms assume radiological views of the slices (viewed from the feet). other
        modalities such as physical sectioning may view from the head. These transforms modify the original
        with a 180° rotation about y
        """

        self.hf_mat = vtk.vtkMatrix4x4()
        self.hf_mat.Zero()
        self.hf_mat.SetElement(0, 0, -1)
        self.hf_mat.SetElement(1, 1, 1)
        self.hf_mat.SetElement(2, 2, -1)
        self.hf_mat.SetElement(3, 3, 1)

    def s_i(self):
        t = vtk.vtkTransform()
        t.SetMatrix(self.si_mat)
        return t

    def i_s(self):
        t = vtk.vtkTransform()
        t.SetMatrix(self.is_mat)
        return t

    @staticmethod
    def a_p():
        t = vtk.vtkTransform()
        return t.Scale(1, -1, 1)

    @staticmethod
    def p_a():
        t = vtk.vtkTransform()
        return t.Scale(1, -1, -1)

    def l_r(self):
        t = vtk.vtkTransform()
        t.SetMatrix(self.lr_mat)
        t.Update()
        return t

    def r_l(self):
        t = vtk.vtkTransform()
        t.SetMatrix(self.lr_mat)
        return t

    def h_f(self):
        t = vtk.vtkTransform()
        t.SetMatrix(self.hf_mat)
        return t

    def hf_si(self):
        t = vtk.vtkTransform()
        t.Concatenate(self.hf_mat)
        t.Concatenate(self.si_mat)
        return t

    def hf_is(self):
        t = vtk.vtkTransform()
        t.Concatenate(self.hf_mat)
        t.Concatenate(self.is_mat)
        return t

    def hf_ap(self):
        t = vtk.vtkTransform()
        t.Concatenate(self.hf_mat)
        t.Scale(1, -1, 1)
        return t

    def hf_pa(self):
        t = vtk.vtkTransform()
        t.Concatenate(self.hf_mat)
        t.Scale(1, -1, -1)
        return t

    def hf_lr(self):
        t = vtk.vtkTransform()
        t.Concatenate(self.hf_mat)
        t.Concatenate(self.lr_mat)
        return t

    def hf_rl(self):
        t = vtk.vtkTransform()
        t.Concatenate(self.hf_mat)
        t.Concatenate(self.rl_mat)
        return t

    def get(self, order):
        """
        Returns the vtkTransform corresponding to the slice order.

        :param order: The slice order
        :return: The vtkTransform to use
        """
        if order == 'si':
            return self.s_i()
        elif order == 'is':
            return self.i_s()
        elif order == 'ap':
            return self.a_p()
        elif order == 'pa':
            return self.p_a()
        elif order == 'lr':
            return self.l_r()
        elif order == 'rl':
            return self.r_l()
        elif order == 'hf':
            return self.h_f()
        elif order == 'hfsi':
            return self.hf_si()
        elif order == 'hfis':
            return self.hf_is()
        elif order == 'hfap':
            return self.hf_ap()
        elif order == 'hfpa':
            return self.hf_pa()
        elif order == 'hflr':
            return self.hf_lr()
        elif order == 'hfrl':
            return self.hf_rl()
        else:
            s = 'No such transform "{:s}" exists.'.format(order)
            raise Exception(s)

# If this script is run as the main program, invoke the main function.
if __name__ == '__main__':
    import sys
    
    main()