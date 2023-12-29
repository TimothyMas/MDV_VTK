import vtk

def main():
    colors = vtk.vtkNamedColors()

    fileName = r'./head-neck-2016-09/grayscale/Osirix-Manix-255-res.nrrd'

    colors.SetColor("BkgColor", [201, 214, 255, 255])

    # Create the renderer, the render window, and the interactor.
    aRenderer = vtk.vtkRenderer()
    renWin = vtk.vtkRenderWindow()
    renWin.AddRenderer(aRenderer)
    iren = vtk.vtkRenderWindowInteractor()
    iren.SetRenderWindow(renWin)

    # Set a background color for the renderer and set the size of the
    # render window (expressed in pixels).
    aRenderer.SetBackground(colors.GetColor3d("BkgColor"))
    renWin.SetSize(1024,720)
    renWin.SetWindowName("Raw data in three planes: Axial, Sagittal, Coronal")

    # Reading slices from .nrrd file
    reader = vtk.vtkNrrdReader()
    reader.SetFileName(fileName)
    reader.Update()

    # Outline
    outlineData = vtk.vtkOutlineFilter()
    outlineData.SetInputConnection(reader.GetOutputPort())
    outlineData.Update()

    mapOutline = vtk.vtkPolyDataMapper()
    mapOutline.SetInputConnection(outlineData.GetOutputPort())

    outline = vtk.vtkActor()
    outline.SetMapper(mapOutline)
    outline.GetProperty().SetColor(colors.GetColor3d("Black"))

    # B/W lookup table.
    bwLut = vtk.vtkLookupTable()
    bwLut.SetTableRange(-980, 5144)
    bwLut.SetSaturationRange(0, 0)
    bwLut.SetHueRange(0, 0)
    bwLut.SetValueRange(0, 1)
    bwLut.Build()  # effective built

    #Defining planes    

    # Axial plane
    ap = int(input("Input slice number for axial plane from range 0-206: "))
    
    axialColors = vtk.vtkImageMapToColors()
    axialColors.SetInputConnection(reader.GetOutputPort())
    axialColors.SetLookupTable(bwLut)
    axialColors.Update()

    axial = vtk.vtkImageActor()
    axial.GetMapper().SetInputConnection(axialColors.GetOutputPort())
    axial.SetDisplayExtent(0, 255, 0, 255, ap, ap)

    # Sagittal plane
    sp = int(input("Input slice number for sagittal plane from range 0-255: "))
    
    sagittalColors = vtk.vtkImageMapToColors()
    sagittalColors.SetInputConnection(reader.GetOutputPort())
    sagittalColors.SetLookupTable(bwLut)
    sagittalColors.Update()

    sagittal = vtk.vtkImageActor()
    sagittal.GetMapper().SetInputConnection(sagittalColors.GetOutputPort())
    sagittal.SetDisplayExtent(sp, sp, 0, 255, 0, 206)

    # Coronal plane
    cp = int(input("Input slice number for coronal plane from range 0-255: "))
    
    coronalColors = vtk.vtkImageMapToColors()
    coronalColors.SetInputConnection(reader.GetOutputPort())
    coronalColors.SetLookupTable(bwLut)
    coronalColors.Update()

    coronal = vtk.vtkImageActor()
    coronal.GetMapper().SetInputConnection(coronalColors.GetOutputPort())
    coronal.SetDisplayExtent(0, 255, cp, cp, 0, 206)

    # Initial view of data
    aCamera = vtk.vtkCamera()
    aCamera.SetViewUp(0, 0, -1)
    aCamera.SetPosition(0, -1, 0)
    aCamera.SetFocalPoint(0, 0, 0)
    aCamera.ComputeViewPlaneNormal()
    aCamera.Azimuth(30.0)
    aCamera.Elevation(30.0)

    # Actors are added to the renderer.
    aRenderer.AddActor(outline)
    aRenderer.AddActor(sagittal)
    aRenderer.AddActor(axial)
    aRenderer.AddActor(coronal)

    aRenderer.SetActiveCamera(aCamera)

    renWin.Render()

    aRenderer.ResetCamera()
    aRenderer.ResetCameraClippingRange()

    # Interact with the data.
    renWin.Render()
    iren.Initialize()
    iren.Start()

if __name__ == '__main__':
    main()