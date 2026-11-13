from conan import ConanFile
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import export_conandata_patches, apply_conandata_patches, copy, get, rmdir
from conan.tools.build import check_min_cppstd
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
        "with_dxheaders": [True, False],
        "enable_spirv": [True, False],
        "build_dxilconv": [True, False],
    }

    default_options = {
        "with_dxheaders": True,
        "enable_spirv": True,
        "build_dxilconv": True,
    }

    def export_sources(self):
        export_conandata_patches(self)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def config_options(self):
        if self.settings.os != "Windows":
            del self.options.with_dxheaders

    def configure(self):
        self.settings.rm_safe("compiler.cppstd")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.settings.os != "Windows":
            self.requires("directx-headers/1.602.0")
        elif self.options.get_safe("with_dxheaders"):
            self.requires("directx-headers/[>=1.602 <2]")
        if self.options.get_safe("enable_spirv"):
            self.requires("spirv-headers/1.4.363.0")
            self.requires("spirv-tools/1.4.363.0")

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
        tc.cache_variables["LLVM_APPEND_VC_REV"] = False
        tc.cache_variables["LLVM_INCLUDE_TESTS"] = False
        tc.cache_variables["LLVM_INSTALL_TOOLCHAIN_ONLY"] = True
        tc.cache_variables["HLSL_INCLUDE_TESTS"] = False
        tc.cache_variables["HLSL_EMBED_VERSION"] = True
        tc.cache_variables["HLSL_OFFICIAL_BUILD"] = False
        tc.cache_variables["HLSL_ENABLE_FIXED_VER"] = True
        tc.cache_variables["HLSL_SUPPORT_QUERY_GIT_COMMIT_INFO"] = False
        tc.cache_variables["HLSL_AUTOCRLF"] = False

        # SPIR-V codegen option
        tc.cache_variables["ENABLE_SPIRV_CODEGEN"] = self.options.enable_spirv
        tc.cache_variables["SPIRV_BUILD_TESTS"] = False

        # DXILCONV option
        tc.cache_variables["HLSL_BUILD_DXILCONV"] = self.options.build_dxilconv

        # Use C++17 as required
        tc.variables["CMAKE_CXX_STANDARD"] = 17
        tc.variables["CMAKE_CXX_STANDARD_REQUIRED"] = True

        # Use Conan deps instead of external directory
        tc.variables["DXC_USE_CONAN_DEPS_FOR_EXTERNAL"] = True
        if self.settings.os == "Windows":
            tc.variables["DXC_USE_CONAN_DIRECTX_HEADERS"] = self.options.with_dxheaders

        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(cli_args=["-C", os.path.join(self.source_folder, "cmake/caches/PredefinedParams.cmake")])
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
