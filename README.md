# MDV - Anatomical Data Atlas Visualization

This project uses Python and the Visualization Toolkit (VTK) to advance medical data visualisation. It's built around the SPL Head and Neck Atlas, providing tools for rendering both 2D slices and 3D models from medical imaging data. 

![MDV Interface](https://github.com/TimothyMas/MDV/blob/main/Images/MDV_UI.png)

## Additional Resources

For more detailed information about the project and sources, refer to the project documentation:

- [MDV Project Detailed Documentation](https://github.com/TimothyMas/MDV/blob/main/MDV_Documentation.pdf)

## Features
- **Python Scripting for Medical Imaging**: Utilizes Python for efficient medical data processing and visualisation.
- **2D and 3D Rendering**: Capable of producing both 2D slices and 3D models, offering a comprehensive view of medical images.
- **SPL Atlas Integration**: Leverages this specific medical dataset for detailed anatomical studies.
- **Interactive Visualization Tools**: Provides tools for interactive exploration of medical images, enhancing understanding and analysis.
- **Customizable Output**: Allows customization of the visualization output to meet specific user needs.

## Customization

The code is designed to be flexible, allowing users to explore different parts of the anatomy. You can customize which part of the body to visualize by searching within the downloaded SPL Head and Neck Atlas "models" folder. You can choose the specific models you are interested in to tailor the visualization to your needs. More detailed information is in the code comments.

For an example of how to select different models, see the screenshot in the `Images` folder:

![Selecting Different Models](https://github.com/TimothyMas/MDV/blob/main/Images/MDV_Choose_model.png)

## Getting Started

### Prerequisites
- Python 3.x
- VTK library
- SPL Head and Neck Atlas data (or another)

**NOTE** [December 2023] Python 3.12.1 is the newest version so some libraries (e.g. Torch) could not download successfully. If the *Could not find a version that satisfies the requirement torch* error occurred simply type `pip3 install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu118`. Otherwise search for nightly versions.

### Installation
1. Install Python 3.x from [Python's official website](https://www.python.org).
2. Install VTK using pip: `pip install vtk`.
3. Download SPL Head and Neck Atlas from [The Open Anatomy Project](http://www.spl.harvard.edu/publications/item/view/2037).

## Usage

### Setting Up with Visual Studio Code (VSC)
1. Install [Visual Studio Code (VSC)](https://code.visualstudio.com/Download).
2. Open VSC, go to the 'Source Control' panel, and click 'Clone Repository'.
3. Paste the URL of this GitHub repository and clone it (or use `git clone "https://github.com/TimothyMas/MDV"` in your desired directory).
4. Open the repository folder in VSC.

### Running the Scripts
After cloning the repository:
1. Navigate to the script directory.
2. Execute the chosen script: `python script_name.py` by simply clicking run.

### Understanding the Code
The codebase includes detailed comments to help understand each function and significant code block. This is especially useful for beginners or those new to Python, VTK, or medical imaging.

## Contributing
Contributions are welcome! Please fork the repository and create a pull request with your improvements.

## License
This project is licensed under the MIT License.
