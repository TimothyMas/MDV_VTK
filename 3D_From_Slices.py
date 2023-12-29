import collections
from pathlib import Path
import vtk

# Define the main function which sets up and renders the visualization
def main(tissues, flying_edges, decimate):
    colors = vtk.vtkNamedColors()

    # File paths for the grayscale CT and the labeled tissue segmentation
    head_fn= r'./head-neck-2016-09/grayscale/Osirix-Manix-255-res.nrrd'
    head_tissue_fn= r'./head-neck-2016-09/labels/HN-Atlas-labels.nrrd'

    # Retrieve tissue parameters and select the specified tissues for visualization
    available_tissues = tissue_parameters()
    selected_tissues = {key: available_tissues[key] for key in tissues}
    if not selected_tissues:
        print('No tissues!')
        return

    # Check for missing parameters in the selected tissues
    missing_parameters = False
    for k, v in selected_tissues.items():
        res = check_for_required_parameters(k, v)
        if res:
            print(res)
            missing_parameters = True
    if missing_parameters:
        print('Some required parameters are missing!')
        return

    # Setup render window, renderer, and interactor.
    renderer = vtk.vtkRenderer()
    render_window = vtk.vtkRenderWindow()
    render_window.AddRenderer(renderer)
    render_window_interactor = vtk.vtkRenderWindowInteractor()
    render_window_interactor.SetRenderWindow(render_window)

    lut = create_head_lut(colors)

    for name, tissue in selected_tissues.items():
        print('Tissue: {:>9s}, label: {:2d}'.format(name, tissue['TISSUE']))
        actor = create_head_actor(head_fn, head_tissue_fn, tissue, flying_edges, decimate, lut)
        renderer.AddActor(actor)

    # Initial view (looking down on the dorsal surface).
    renderer.GetActiveCamera().Roll(-90)
    renderer.ResetCamera()

    colors.SetColor("BkgColor", [201, 214, 255, 255])
    renderer.SetBackground(colors.GetColor3d('BkgColor'))

    render_window.SetSize(1024, 720)
    render_window.SetWindowName('Head and Neck Reconstruction')
    render_window.Render()

    # Add orientation axes to the rendering window
    axes = vtk.vtkAxesActor()

    widget = vtk.vtkOrientationMarkerWidget()
    rgba = [0.0, 0.0, 0.0, 0.0]
    colors.GetColor("Carrot", rgba)
    widget.SetOutlineColor(rgba[0], rgba[1], rgba[2])
    widget.SetOrientationMarker(axes)
    widget.SetInteractor(render_window_interactor)
    widget.SetViewport(0.0, 0.0, 0.2, 0.2)
    widget.SetEnabled(1)
    widget.InteractiveOn()

    # Final rendering and start the interaction loop
    render_window.Render()
    render_window_interactor.Start()

# Function to create an actor for the head visualization
def create_head_actor(head_fn, head_tissue_fn, tissue, flying_edges, decimate, lut):

    # Choose the file based on whether the tissue is the skull or not
    if tissue['NAME'] == 'skull':
        fn = head_fn
    else:
        fn = head_tissue_fn

    reader = vtk.vtkNrrdReader()
    reader.SetFileName(str(fn))
    reader.Update()

    last_connection = reader

    # If not processing the skull, threshold the image to select the tissue
    if not tissue['NAME'] == 'skull':
        select_tissue = vtk.vtkImageThreshold()
        select_tissue.ThresholdBetween(tissue['TISSUE'], tissue['TISSUE'])
        select_tissue.SetInValue(255)
        select_tissue.SetOutValue(0)
        select_tissue.SetInputConnection(last_connection.GetOutputPort())
        last_connection = select_tissue

    # Optionally shrink the image data for faster processing
    shrinker = vtk.vtkImageShrink3D()
    shrinker.SetInputConnection(last_connection.GetOutputPort())
    shrinker.SetShrinkFactors(tissue['SAMPLE_RATE'])
    shrinker.AveragingOn()
    last_connection = shrinker

    # Optionally apply a Gaussian filter for smoothing
    if not all(v == 0 for v in tissue['GAUSSIAN_STANDARD_DEVIATION']):
        gaussian = vtk.vtkImageGaussianSmooth()
        gaussian.SetStandardDeviation(*tissue['GAUSSIAN_STANDARD_DEVIATION'])
        gaussian.SetRadiusFactors(*tissue['GAUSSIAN_RADIUS_FACTORS'])
        gaussian.SetInputConnection(shrinker.GetOutputPort())
        last_connection = gaussian

    # Create an isosurface using either flying edges or marching cubes
    iso_value = tissue['VALUE']
    if flying_edges:
        iso_surface = vtk.vtkFlyingEdges3D()
        iso_surface.SetInputConnection(last_connection.GetOutputPort())
        iso_surface.ComputeScalarsOff()
        iso_surface.ComputeGradientsOff()
        iso_surface.ComputeNormalsOff()
        iso_surface.SetValue(0, iso_value)
        iso_surface.Update()
    else:
        iso_surface = vtk.vtkMarchingCubes()
        iso_surface.SetInputConnection(last_connection.GetOutputPort())
        iso_surface.ComputeScalarsOff()
        iso_surface.ComputeGradientsOff()
        iso_surface.ComputeNormalsOff()
        iso_surface.SetValue(0, iso_value)
        iso_surface.Update()

    # Apply a transform to correct for the slice order
    so = SliceOrder()
    transform = so.get('hfap')
    transform.Scale(1, -1, 1)
    tf = vtk.vtkTransformPolyDataFilter()
    tf.SetTransform(transform)
    tf.SetInputConnection(iso_surface.GetOutputPort())
    last_connection = tf
    
    # Optionally decimate the mesh to reduce complexity
    if decimate:
        decimator = vtk.vtkDecimatePro()
        decimator.SetInputConnection(last_connection.GetOutputPort())
        decimator.SetFeatureAngle(tissue['DECIMATE_ANGLE'])
        decimator.MaximumIterations = tissue['DECIMATE_ITERATIONS']
        decimator.PreserveTopologyOn()
        decimator.SetErrorIsAbsolute(1)
        decimator.SetAbsoluteError(tissue['DECIMATE_ERROR'])
        decimator.SetTargetReduction(tissue['DECIMATE_REDUCTION'])
        last_connection = decimator

    # Smooth the mesh with a windowed sinc filter
    smoother = vtk.vtkWindowedSincPolyDataFilter()
    smoother.SetInputConnection(last_connection.GetOutputPort())
    smoother.SetNumberOfIterations(tissue['SMOOTH_ITERATIONS'])
    smoother.BoundarySmoothingOff()
    smoother.FeatureEdgeSmoothingOff()
    smoother.SetFeatureAngle(tissue['SMOOTH_ANGLE'])
    smoother.SetPassBand(tissue['SMOOTH_FACTOR'])
    smoother.NonManifoldSmoothingOn()
    smoother.NormalizeCoordinatesOff()
    smoother.Update()

    # Compute normals for better lighting effects
    normals = vtk.vtkPolyDataNormals()
    normals.SetInputConnection(smoother.GetOutputPort())
    normals.SetFeatureAngle(tissue['FEATURE_ANGLE'])

    # Create triangle strips for efficient rendering
    stripper = vtk.vtkStripper()
    stripper.SetInputConnection(normals.GetOutputPort())

    # Map the data to geometry
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(stripper.GetOutputPort())

    # Create iso-surface
    contour = vtk.vtkContourFilter()
    contour.SetInputConnection(reader.GetOutputPort())
    contour.SetValue(0, iso_value)

    # Create an actor for the tissue with properties such as color and opacity
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetOpacity(tissue['OPACITY'])
    actor.GetProperty().SetDiffuseColor(lut.GetTableValue(tissue['TISSUE'])[:3])
    actor.GetProperty().SetSpecular(0.5)
    actor.GetProperty().SetSpecularPower(10)

    return actor

# The remaining code defines specific tissue characteristics and parameters
# used in the visualization, such as tissue name, label, and visual properties.

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

def default_parameters():
    p = dict()
    p['NAME'] = ''
    p['TISSUE'] = '1'
    p['STUDY'] = 'headtissue'
    p['VALUE'] = 127.5
    p['FEATURE_ANGLE'] = 60
    p['DECIMATE_ANGLE'] = 60
    p['SMOOTH_ANGLE'] = 60
    p['SMOOTH_ITERATIONS'] = 20
    p['SMOOTH_FACTOR'] = 0.001
    p['DECIMATE_ITERATIONS'] = 1
    p['DECIMATE_REDUCTION'] = 1
    p['DECIMATE_ERROR'] = 0.0002
    p['DECIMATE_ERROR_INCREMENT'] = 0.0002
    p['GAUSSIAN_STANDARD_DEVIATION'] = [1, 1, 1]
    p['GAUSSIAN_RADIUS_FACTORS'] = [1, 1, 1]
    p['SAMPLE_RATE'] = [1, 1, 1]
    p['OPACITY'] = 1.0
    return p

def hyoid():
    p = head()
    p['NAME'] = 'Hyoid'
    p['TISSUE'] = 9
    p['VALUE'] = 27.5
    return p

def atlas():
    p = head()
    p['NAME'] = 'Atlas'
    p['TISSUE'] = 11
    p['VALUE'] = 90
    p['GAUSSIAN_STANDARD_DEVIATION'] = [1, 1, 1]
    return p

def axis():
    p = head()
    p['NAME'] = 'Axis'
    p['TISSUE'] = 12
    p['VALUE']= 19.5
    return p

def cervical3():
    p = head()
    p['NAME'] = 'Cervical3'
    p['TISSUE'] = 13
    p['VALUE']= 63.5
    p['GAUSSIAN_STANDARD_DEVIATION'] = [1, 1, 1]
    p['DECIMATE_ITERATIONS'] = 3
    return p

def cervical4():
    p = head()
    p['NAME'] = 'Cervical4'
    p['TISSUE'] = 14
    p['VALUE'] = 70
    p['OPACITY']= 0.5
    return p

def mandible():
    p = head()
    p['NAME'] = 'Mandible'
    p['TISSUE'] = 25
    p['VALUE'] = 29.5
    return p

def head():
    p = default_parameters()
    p['STUDY'] = 'headtissue'
    p['SLICE_ORDER'] = 'si'
    p['VALUE'] = 144
    p['SAMPLE_RATE'] = [1, 1, 1]
    p['GAUSSIAN_STANDARD_DEVIATION'] = [2, 2, 2]
    p['DECIMATE_REDUCTION'] = 0.95
    p['DECIMATE_ITERATIONS'] = 5
    p['DECIMATE_ERROR'] = 0.0002
    p['DECIMATE_ERROR_INCREMENT'] = 0.0002
    p['SMOOTH_FACTOR'] = 0.001
    return p

def rightclavicle():
    p = head()
    p['NAME'] = 'Right_clavicle'
    p['TISSUE'] = 26
    p['VALUE'] = 96
    p['SMOOTH_ITERATIONS'] = 10
    p['GAUSSIAN_STANDARD_DEVIATION'] = [1, 1, 1]
    return p

def leftclavicle():
    p = head()
    p['NAME'] = 'Left_clavicle'
    p['TISSUE'] = 27
    p['VALUE'] = 48
    return p

def sternum():
    p = head()
    p['NAME'] = 'Sternum'
    p['TISSUE'] = 28
    p['VALUE'] = 36.5
    return p

def rib1():
    p = head()
    p['NAME'] = 'Rib_1'
    p['TISSUE'] = 31
    return p

def rib2():
    p = head()
    p['NAME'] = 'Rib_2'
    p['TISSUE'] = 32
    p['VALUE'] = 45
    return p

def rib3():
    p = head()
    p['NAME'] = 'Rib_3'
    p['TISSUE'] = 33
    return p

def rib4():
    p = head()
    p['NAME'] = 'Rib_4'
    p['TISSUE'] = 34
    p['VALUE']= 21
    p['SMOOTH_ITERATIONS'] = 10
    p['GAUSSIAN_STANDARD_DEVIATION'] = [1, 1, 1]
    return p

def rib5():
    p = head()
    p['NAME'] = 'Rib_5'
    p['TISSUE'] = 35
    p['VALUE'] = 108
    p['SMOOTH_ITERATIONS'] = 10
    p['GAUSSIAN_STANDARD_DEVIATION'] = [1, 1, 1]
    return p

def tissue_parameters():
    t = dict()
    t['Hyoid'] = hyoid()
    t['Atlas'] = atlas()
    t['Axis'] = axis()
    t['Cervical3'] = cervical3()
    t['Cervical4'] = cervical4()
    t['head'] = head()
    t['Mandible'] = mandible()
    t['Right_Clavicle'] = rightclavicle()
    t['Left_Clavicle'] = leftclavicle()
    t['Sternum'] = sternum()
    t['Rib1'] = rib1()
    t['Rib2'] = rib2()
    t['Rib3'] = rib3()
    t['Rib4'] = rib4()
    t['Rib5'] = rib5()

    return t

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

def check_for_required_parameters(tissue, parameters):
    required = {'NAME', 'TISSUE', 'STUDY', 'VALUE',
                'GAUSSIAN_STANDARD_DEVIATION','DECIMATE_ITERATIONS'}
    k = set(parameters.keys())
    s = None
    if len(k) == 0:
        s = 'Missing parameters for {:11s}: {:s}'.format(tissue, ', '.join(map(str, required)))
    else:
        d = required.difference(k)
        if d:
            s = 'Missing parameters for {:11s}: {:s}'.format(tissue, ', '.join(map(str, d)))
    return s

if __name__ == '__main__':
    import sys
    
    tissues= ['Hyoid', 'Atlas',
              'Axis','Cervical3','Cervical4',
              'Mandible','Right_Clavicle', 'Left_Clavicle',
              'Sternum','Rib1',
              'Rib2','Rib3',
              'Rib4','Rib5']
    
    # Enable flying edges and decimation options
    flying_edges=True
    decimate=0
    
    # Call the main function to start the visualization
    main(tissues, flying_edges, decimate)