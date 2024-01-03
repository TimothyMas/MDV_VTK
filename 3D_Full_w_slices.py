import vtk
import os
import pandas as pd
import random

def load_data(file_path):
    reader = vtk.vtkNrrdReader()
    reader.SetFileName(file_path)
    reader.Update()

    return reader

def create_outline(reader):
    outline = vtk.vtkOutlineFilter()
    outline.SetInputConnection(reader.GetOutputPort())
    outline_mapper = vtk.vtkPolyDataMapper()
    outline_mapper.SetInputConnection(outline.GetOutputPort())
    outline_actor = vtk.vtkActor()
    outline_actor.SetMapper(outline_mapper)

    return outline_actor

def create_slice_actor(reader, slice_index, orientation):
    reslice = vtk.vtkImageReslice()
    reslice.SetInputConnection(reader.GetOutputPort())
    reslice.SetOutputDimensionality(2)
    reslice.SetResliceAxesDirectionCosines([1,0,0, 0,1,0, 0,0,1])  # Default axes, change as needed for orientation
    reslice.SetResliceAxesOrigin(slice_index)  # Set the slice index for the desired orientation
    reslice.SetInterpolationModeToLinear()

    lut = create_lookup_table()

    color = vtk.vtkImageMapToColors()
    color.SetLookupTable(lut)
    color.SetInputConnection(reslice.GetOutputPort())

    actor = vtk.vtkImageActor()
    actor.GetMapper().SetInputConnection(color.GetOutputPort())
    
    return actor

def create_lookup_table():
    lut = vtk.vtkLookupTable()
    lut.SetNumberOfTableValues(256)
    lut.Build()

    # Default color for labels not in use (black or transparent)
    for i in range(256):
        lut.SetTableValue(i, 0.0, 0.0, 0.0, 0.0)

    def generate_color(index, total):
        random.seed(index)

        return (random.random(), random.random(), random.random(), 1.0)

    # List of label ranges
    label_ranges = [range(9, 18), range(21, 29), range(31, 37), 
                    range(50, 65), range(101, 121)]

    total_labels = sum(len(r) for r in label_ranges)
    label_index = 0
    for label_range in label_ranges:
        for label in label_range:
            color = generate_color(label_index, total_labels)
            lut.SetTableValue(label, *color)
            label_index += 1

    return lut

def create_mesh_from_segmentation(reader):
    marching_cubes = vtk.vtkDiscreteMarchingCubes()
    marching_cubes.SetInputConnection(reader.GetOutputPort())
    
    scalar_range = reader.GetOutput().GetScalarRange()
    min_label = int(scalar_range[0])
    max_label = int(scalar_range[1])
    
    for i in range(min_label, max_label + 1):
        marching_cubes.SetValue(i, i)
    
    marching_cubes.Update()
    
    # Smooth the mesh using vtkWindowedSincPolyDataFilter
    smoother = vtk.vtkWindowedSincPolyDataFilter()
    smoother.SetInputConnection(marching_cubes.GetOutputPort())
    smoother.SetNumberOfIterations(20)              # Adjust the number of iterations for more or less smoothing
    smoother.BoundarySmoothingOn()
    smoother.FeatureEdgeSmoothingOn()
    smoother.SetFeatureAngle(120.0)                 # Adjust this angle to smooth less or more sharply defined areas
    smoother.SetPassBand(0.1)                       # Adjust the passband for more or less smoothing
    smoother.NonManifoldSmoothingOn()
    smoother.NormalizeCoordinatesOn()
    smoother.Update()
    
    return smoother.GetOutput()

def color_mesh(mesh, lut):
    color_mapper = vtk.vtkPolyDataMapper()
    color_mapper.SetInputData(mesh)
    color_mapper.SetLookupTable(lut)
    color_mapper.SetScalarRange(0, 255)  # Ensure this range matches the LUT
    
    mesh_actor = vtk.vtkActor()
    mesh_actor.SetMapper(color_mapper)
    
    return mesh_actor

def main():
    # File paths for the grayscale and segmentation data
    grayscale_file_path = r'./head-neck-2016-09/grayscale/Osirix-Manix-255-res.nrrd'
    segmentation_file_path = r'./head-neck-2016-09/labels/HN-Atlas-labels.nrrd'
    
    # Create a renderer, render window, and interactor
    renderer = vtk.vtkRenderer()
    render_window = vtk.vtkRenderWindow()
    render_window.AddRenderer(renderer)
    render_window_interactor = vtk.vtkRenderWindowInteractor()
    render_window_interactor.SetRenderWindow(render_window)
    
    # Load the grayscale data
    grayscale_reader = load_data(grayscale_file_path)
    
    # Load the segmentation data
    segmentation_reader = load_data(segmentation_file_path)
    
    # Create the outline of the data
    outline_actor = create_outline(grayscale_reader)
    renderer.AddActor(outline_actor)
    
    # Create the color lookup table
    lut = create_lookup_table()
    
    # Get the extent of the grayscale data to position the planes correctly
    extent = grayscale_reader.GetOutput().GetExtent()
    x_middle = int((extent[0] + extent[1]) / 2)
    y_middle = int((extent[2] + extent[3]) / 2)
    z_middle = int((extent[4] + extent[5]) / 2)

    # Set up the planes using the image data and add them to the renderer
    colors = vtk.vtkImageMapToColors()
    colors.SetLookupTable(lut)
    colors.SetInputConnection(grayscale_reader.GetOutputPort())

    plane_widget_x = vtk.vtkImagePlaneWidget()
    plane_widget_x.SetInteractor(render_window_interactor)
    plane_widget_x.SetInputConnection(colors.GetOutputPort())
    plane_widget_x.SetPlaneOrientationToXAxes()
    plane_widget_x.SetSliceIndex(x_middle)
    plane_widget_x.UpdatePlacement()
    plane_widget_x.On()
    
    plane_widget_y = vtk.vtkImagePlaneWidget()
    plane_widget_y.SetInteractor(render_window_interactor)
    plane_widget_y.SetInputConnection(colors.GetOutputPort())
    plane_widget_y.SetPlaneOrientationToYAxes()
    plane_widget_y.SetSliceIndex(y_middle)
    plane_widget_y.UpdatePlacement()
    plane_widget_y.On()
    
    plane_widget_z = vtk.vtkImagePlaneWidget()
    plane_widget_z.SetInteractor(render_window_interactor)
    plane_widget_z.SetInputConnection(colors.GetOutputPort())
    plane_widget_z.SetPlaneOrientationToZAxes()
    plane_widget_z.SetSliceIndex(z_middle)
    plane_widget_z.UpdatePlacement()
    plane_widget_z.On()
    
    # Create mesh from segmentation and color it
    mesh = create_mesh_from_segmentation(segmentation_reader)
    mesh_actor = color_mesh(mesh, lut)
    renderer.AddActor(mesh_actor)

    # Create mesh from segmentation and color it
    mesh = create_mesh_from_segmentation(segmentation_reader)
    mesh_actor = color_mesh(mesh, lut)
    renderer.AddActor(mesh_actor)
    
    # Optional: Adjust the camera to better frame the 3D solids or set up a specific view
    renderer.ResetCamera()
    
    # Set background color to black
    renderer.SetBackground(0, 0, 0)
    
    # Render and start interaction
    render_window.Render()
    render_window_interactor.Initialize()
    render_window_interactor.Start()

if __name__ == "__main__":
    main()
