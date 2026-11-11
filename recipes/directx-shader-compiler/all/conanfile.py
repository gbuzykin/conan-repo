from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get, rmdir
from conan.tools.scm import Version
import os


required_conan_version = ">=2.0"


class DirectXShaderCompilerConan(ConanFile):
    name = "directx-shader-compiler"
    description = "DirectX Shader Compiler - HLSL to DXIL compiler"
    license = "NCSA"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/microsoft/DirectXShaderCompiler"
    topics = ("directx", "hlsl", "shader", "compiler", "dxil")
    package_type = "application"
    settings = "os", "arch", "compiler", "build_type"

    options = {
        "enable_spirv": [True, False],
        "build_dxilconv": [True, False],
    }

    default_options = {
        "enable_spirv": False,
        "build_dxilconv": True,
    }

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def validate(self):
        if self.settings.os == "Windows":
            # Windows is fully supported
            pass
        elif self.settings.os == "Linux":
            # Linux is supported
            pass
        else:
            self.output.warning(f"{self.settings.os} is not officially tested")

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["LLVM_APPEND_VC_REV"] = False
        tc.variables["LLVM_INCLUDE_TESTS"] = False
        tc.variables["HLSL_INCLUDE_TESTS"] = False
        tc.variables["LLVM_INCLUDE_DOCS"] = False
        tc.variables["LLVM_INCLUDE_EXAMPLES"] = False
        tc.variables["LLVM_BUILD_TESTS"] = False
        tc.variables["LLVM_BUILD_EXAMPLES"] = False
        tc.variables["LLVM_TARGETS_TO_BUILD"] = "None"
        tc.variables["LLVM_OPTIMIZED_TABLEGEN"] = True
        tc.variables["HLSL_EMBED_VERSION"] = True
        tc.variables["HLSL_OFFICIAL_BUILD"] = False
        tc.variables["HLSL_ENABLE_FIXED_VER"] = False
        tc.variables["HLSL_SUPPORT_QUERY_GIT_COMMIT_INFO"] = False

        # SPIR-V codegen option
        tc.variables["ENABLE_SPIRV_CODEGEN"] = self.options.enable_spirv
        tc.variables["SPIRV_BUILD_TESTS"] = False

        # DXILCONV option
        tc.variables["HLSL_BUILD_DXILCONV"] = self.options.build_dxilconv

        # Use C++17 as required
        tc.variables["CMAKE_CXX_STANDARD"] = 17
        tc.variables["CMAKE_CXX_STANDARD_REQUIRED"] = True

        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

        # Copy license
        copy(self, "LICENSE.TXT",
             src=self.source_folder,
             dst=os.path.join(self.package_folder, "licenses"))

        # Clean up unnecessary files
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.libs = []

        # Add bin directory to PATH
        bin_path = os.path.join(self.package_folder, "bin")
        self.output.info(f"Appending PATH environment variable: {bin_path}")
        self.runenv_info.prepend_path("PATH", bin_path)
        self.buildenv_info.prepend_path("PATH", bin_path)

        # Set DXC executable info
        dxc_exe = "dxc.exe" if self.settings.os == "Windows" else "dxc"
        self.conf_info.define("user.directx-shader-compiler:dxc", os.path.join(bin_path, dxc_exe))
