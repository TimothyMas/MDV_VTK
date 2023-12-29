from pathlib import Path
import vtk

def main(tissues):
    colors = vtk.vtkNamedColors()

    # Setup render window, renderers, and interactor.
    # ren_1 is for the head rendering, ren_2 is for the slider rendering.
    ren_1 = vtk.vtkRenderer()
    ren_2 = vtk.vtkRenderer()

    render_window = vtk.vtkRenderWindow()
    render_window.AddRenderer(ren_1)
    render_window.AddRenderer(ren_2)

    # Define the viewport ranges for the two renderers.
    ren_1.SetViewport(0.0, 0.0, 0.7, 1.0)       #main rendering viewport
    ren_2.SetViewport(0.7, 0.0, 1, 1)           #slider viewport

    render_window_interactor = vtk.vtkRenderWindowInteractor()
    render_window_interactor.SetRenderWindow(render_window)

    # Create a mapping from tissue names to their properties.
    tm = create_tissue_map()
    path = r'./head-neck-2016-09/models/'
    lut = create_head_lut(colors)

    # Dictionary to store slider widgets for each tissue.
    sliders = dict()

    # Define the position step size for the sliders.
    step_size = 1.10 / 17
    pos_y = 0.05

    # List to store the output strings for printing.
    res = ['Using the following tissues:']
    for tissue in tissues:
        source = None
        source = r'{}{}.vtk'.format(path,tissue)

        actor = create_head_actor(str(source), tissue, tm[tissue][1])
        actor.GetProperty().SetOpacity(tm[tissue][2])
        actor.GetProperty().SetDiffuseColor(lut.GetTableValue(tm[tissue][0])[:3])
        actor.GetProperty().SetSpecular(0.2)
        actor.GetProperty().SetSpecularPower(10)
        ren_1.AddActor(actor)
        res.append('{:>11s}, label: {:2d}'.format(tissue, tm[tissue][0]))

        slider_properties = SliderProperties()
        slider_properties.value_initial = tm[tissue][2]
        slider_properties.title = tissue

        # Define screen coordinates for the slider.
        slider_properties.p1 = [0.05, pos_y]
        slider_properties.p2 = [0.25, pos_y]
        pos_y += step_size
        cb = SliderCB(actor.GetProperty())

        slider_widget = make_slider_widget(slider_properties, colors, lut, tm[tissue][0])
        slider_widget.SetInteractor(render_window_interactor)
        slider_widget.SetAnimationModeToAnimate()
        slider_widget.EnabledOn()
        slider_widget.SetCurrentRenderer(ren_2)
        slider_widget.AddObserver(vtk.vtkCommand.InteractionEvent, cb)
        sliders[tissue] = slider_widget

    # Print the list of tissues used if any are present.
    if len(res) > 1:
        print('\n'.join(res))

    render_window.SetSize(1024,720)
    render_window.SetWindowName('Head-Neck')
    
    # Set background colors for both renderers.
    colors.SetColor("BkgColor", [201, 214, 255, 255])
    ren_1.SetBackground(colors.GetColor3d('BkgColor'))
    ren_2.SetBackground(colors.GetColor3d('MidnightBlue'))

    # Initial view (looking down on the dorsal surface).
    ren_1.GetActiveCamera().Roll(-180)
    ren_1.ResetCamera()

    render_window.Render()

    axes = vtk.vtkAxesActor()

    # Add orientation axes to help visualize the coordinate system.
    widget = vtk.vtkOrientationMarkerWidget()
    rgba = [0.0, 0.0, 0.0, 0.0]
    colors.GetColor("Carrot", rgba)
    widget.SetOutlineColor(rgba[0], rgba[1], rgba[2])
    widget.SetOrientationMarker(axes)
    widget.SetInteractor(render_window_interactor)
    widget.SetViewport(0.0, 0.0, 0.2, 0.2)
    widget.SetEnabled(1)
    widget.InteractiveOn()

    render_window_interactor.Start()

# Define a function to create the actor for each tissue model.
def create_head_actor(file_name, tissue, transform):
    so = SliceOrder()

    reader = vtk.vtkPolyDataReader()
    reader.SetFileName(file_name)
    reader.Update()

    # Retrieve the appropriate transformation for the tissue.
    trans = so.get(transform)

    # Special handling for the skull model to flip it appropriately. *YOU COULD CHANGE THIS* if you want to use another atlas.
    if tissue == 'Model_10_skull':
        trans.Scale(1, -1, 1)
        trans.RotateY(180)
    tf = vtk.vtkTransformPolyDataFilter()
    tf.SetInputConnection(reader.GetOutputPort())
    tf.SetTransform(trans)
    tf.SetInputConnection(reader.GetOutputPort())

    # Calculate normals for the tissue model for proper lighting and shading.
    normals = vtk.vtkPolyDataNormals()
    normals.SetInputConnection(tf.GetOutputPort())
    normals.SetFeatureAngle(60.0)

    # Set up the mapper which maps the model data to graphics primitives.
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(normals.GetOutputPort())

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

    return actor

# SliceOrder class contains transformation matrices for different slice orders.
# These transformations ensure the correct orientation of the model data.
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

# Function to create a lookup table for tissue colors.
def create_head_lut(colors):
    lut = vtk.vtkLookupTable()
    lut.SetNumberOfColors(141)
    lut.SetTableRange(0, 140)
    lut.Build()

    lut.SetTableValue(0, colors.GetColor4d('alpha'))            #Background
    lut.SetTableValue(10, colors.GetColor4d('gold'))            #Skull
    lut.SetTableValue(9, colors.GetColor4d('tan'))           #Hyoid
    lut.SetTableValue(11, colors.GetColor4d('salmon'))           #Atlas
    lut.SetTableValue(12, colors.GetColor4d('lawngreen'))       #Axis
    lut.SetTableValue(13, colors.GetColor4d('wheat'))    #Cervical3
    lut.SetTableValue(14, colors.GetColor4d('coral'))       #Cervical4
    lut.SetTableValue(25, colors.GetColor4d('mediumturquoise'))  #Mandible
    lut.SetTableValue(26, colors.GetColor4d('hotpink'))          #Right clavicle
    lut.SetTableValue(27, colors.GetColor4d('mistyrose'))       #Left clavicle
    lut.SetTableValue(28, colors.GetColor4d('paleturquoise'))   #Sternum
    lut.SetTableValue(31, colors.GetColor4d('rose'))       #Rib 1
    lut.SetTableValue(32, colors.GetColor4d('maroon'))             #Rib 2
    lut.SetTableValue(33, colors.GetColor4d('deepskyblue'))     #Rib 3
    lut.SetTableValue(34, colors.GetColor4d('indigo'))       #Rib 4
    lut.SetTableValue(35, colors.GetColor4d('white'))           #Rib 5

    return lut

# Function to create a dictionary mapping tissue names to their properties.
def create_tissue_map():
    tiss = dict()
    # key: name of the tissue. YOU COULD CHANGE THIS. Simply type other model.
    # value: [lut_index, transform, opacity]
    tiss['Model_10_skull'] = [10, 'hfsi', 0.0]
    tiss['Model_9_hyoid'] = [9, 'is', 1.0]
    tiss['Model_11_atlas'] = [11, 'is', 1.0]
    tiss['Model_12_axis'] = [12, 'is', 1.0]
    tiss['Model_13_cervical3'] = [13, 'is', 1.0]
    tiss['Model_14_cervical4'] = [14, 'is', 1.0]
    tiss['Model_25_mandible'] = [25, 'is', 1.0]
    tiss['Model_26_right_clavicle'] = [26, 'is', 1.0]
    tiss['Model_27_left_clavicle'] = [27, 'is', 1.0]
    tiss['Model_28_sternum'] = [28, 'is', 1.0]
    tiss['Model_31_rib1'] = [31, 'is', 1.0]
    tiss['Model_32_rib2'] = [32, 'is', 1.0]
    tiss['Model_33_rib3'] = [33, 'is', 1.0]
    tiss['Model_34_rib4'] = [34, 'is', 1.0]
    tiss['Model_35_rib5'] = [35, 'is', 1.0]

    return tiss

# SliderProperties class to hold the properties for the slider widgets.
class SliderProperties:
    tube_width = 0.008
    cap_width = 0.023
    slider_width = 0.02
    slider_length = 0.02
    title_height = 0.014
    label_height = 0.014

    value_minimum = 0.0
    value_maximum = 1.0
    value_initial = 1.0

    p1 = [0.1, 0.1]
    p2 = [0.3, 0.1]

    title = None

    title_color = 'white'
    value_color = 'white'
    slider_color = 'cornflowerblue'
    selected_color = 'lightsteelblue'
    bar_color = 'lavender'
    bar_ends_color = 'ghostwhite'

# Function to create a slider widget based on the provided properties.
def make_slider_widget(properties, colors, lut, idx):

    # Create the slider representation and configure its properties.
    slider = vtk.vtkSliderRepresentation2D()

    slider.SetMinimumValue(properties.value_minimum)
    slider.SetMaximumValue(properties.value_maximum)
    slider.SetValue(properties.value_initial)
    slider.SetTitleText(properties.title)

    slider.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
    slider.GetPoint1Coordinate().SetValue(properties.p1[0], properties.p1[1])
    slider.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
    slider.GetPoint2Coordinate().SetValue(properties.p2[0], properties.p2[1])

    slider.SetTubeWidth(properties.tube_width)
    slider.SetEndCapWidth(properties.cap_width)
    slider.SetSliderLength(properties.slider_length)
    slider.SetSliderWidth(properties.slider_width)
    slider.SetTitleHeight(properties.title_height)
    slider.SetLabelHeight(properties.label_height)

    # Set the color properties
    # Change the color of the bar.
    slider.GetTubeProperty().SetColor(colors.GetColor3d(properties.bar_color))
    slider.GetTitleProperty().SetFrameWidth(0)
    # Change the color of the ends of the bar.
    slider.GetCapProperty().SetColor(colors.GetColor3d(properties.bar_ends_color))
    # Change the color of the knob that slides.
    slider.GetSliderProperty().SetColor(colors.GetColor3d(properties.slider_color))
    # Change the color of the knob when the mouse is held on it.
    slider.GetSelectedProperty().SetColor(colors.GetColor3d(properties.selected_color))
    # Change the color of the text displaying the value.
    slider.GetLabelProperty().SetColor(colors.GetColor3d(properties.value_color))
    # Change the color of the text indicating what the slider controls
    
    if idx in range(0,141):
        slider.GetTitleProperty().SetColor(lut.GetTableValue(idx)[:3])
        slider.GetTitleProperty().ShadowOff()
    else:
        slider.GetTitleProperty().SetColor(colors.GetColor3d(properties.title_color))

    slider_widget = vtk.vtkSliderWidget()
    slider_widget.SetRepresentation(slider)

    return slider_widget

# SliderCB class defines a callback function to update the tissue opacity.
class SliderCB:
    def __init__(self, actor_property):
        self.actorProperty = actor_property

    # The callback function updates the actor's opacity based on the slider's value.
    def __call__(self, caller, ev):
        slider_widget = caller
        value = slider_widget.GetRepresentation().GetValue()
        self.actorProperty.SetOpacity(value)

# Main section that checks if the script is being run as the main module.
if __name__ == '__main__':
    import sys
    
    tissues= ['Model_10_skull','Model_9_hyoid', 'Model_11_atlas',
              'Model_12_axis','Model_13_cervical3','Model_14_cervical4',
              'Model_25_mandible','Model_26_right_clavicle', 'Model_27_left_clavicle',
              'Model_28_sternum','Model_31_rib1',
              'Model_32_rib2','Model_33_rib3',
              'Model_34_rib4','Model_35_rib5']
    
    # Call the main function to start the visualization process.
    main(tissues)
