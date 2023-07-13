/*
# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and / or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110 - 1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# Copyright 2022, Alex Zhornyak, Valeriy Yatsenko
*/

/* STL */
#include <stdlib.h>

#include <string>
#include <vector>
#include <iostream>
#include <memory>
#include <cctype>
#include <iostream>

/* Files below are licensed with GPL v3.0 license and are taken from: */
/* https://github.com/MichaelRabinovich/Scalable-Locally-Injective-Mappings */
#include "Param_State.h"
#include "GlobalLocalParametrization.h"
#include "eigen_stl_utils.h"
#include "parametrization_utils.h"
#include "StateManager.h"

/* Files below are licensed with GPL v3.0 license and are taken from: */
/* https://github.com/libigl/libigl */
#include <igl/components.h>
#include <igl/read_triangle_mesh.h>

/* Local cross-platform config */
#include "config.h"


namespace Zenuvutils {

	std::string StrToLower(std::string s) {
		std::transform(s.begin(), s.end(), s.begin(),
			[](unsigned char c) { return std::tolower(c); } // correct
		);
		return s;
	}

	std::vector<std::string> SplitPath(const std::string& str, const std::set<char> delimiters) {
		std::vector<std::string> result;

		char const* pch = str.c_str();
		char const* start = pch;
		for (; *pch; ++pch)
		{
			if (delimiters.find(*pch) != delimiters.end())
			{
				if (start != pch)
				{
					std::string str(start, pch);
					result.push_back(str);
				}
				else
				{
					result.push_back("");
				}
				start = pch + 1;
			}
		}
		result.push_back(start);

		return result;
	}

	void ZenCheckCompliance(const std::string &sFullPath, const std::string &sFileName) {
		std::set<char> delimiters{ '/', '\\' };
		auto fileParts = SplitPath(sFullPath, delimiters);
		for (auto it = fileParts.begin(); it != fileParts.end(); it++) {
			*it = StrToLower(*it);
		}

		const std::vector<std::string> vLib{ "zenuv", "utils", "clib", StrToLower(sFileName) };

		auto itCompare = std::find_end(fileParts.begin(), fileParts.end(),
			vLib.begin(), vLib.end()
		);

		if (itCompare == fileParts.end())
			throw std::runtime_error("Compliance complete mismatch!");

		const auto countFromEnd = fileParts.size() - std::distance(fileParts.begin(), itCompare);
		if (countFromEnd != vLib.size())
			throw std::runtime_error("Position compliance mismatch!");

		return; /* Successfully compliant */

		throw std::runtime_error("Can not perform compliance test 1!");
	}
}

typedef struct {
	bool _checkMultipleComponents = true;
	bool _checkTopology = true;
	bool _checkEdgeManifold = true;
	bool _checkZeroAreaFaces = true;
} RelaxChecks;

void check_mesh_for_issues(Eigen::MatrixXd& V, Eigen::MatrixXi& F, Eigen::VectorXd& areas, const RelaxChecks &relaxChecks) {
	if (relaxChecks._checkMultipleComponents) {
		Eigen::SparseMatrix<double> A;
		igl::adjacency_matrix(F, A);

		Eigen::MatrixXi C, Ci;
		igl::components(A, C, Ci);
		int connected_components = Ci.rows();
		if (connected_components != 1) {
			throw std::runtime_error("Check Multiple Components - FAILED!");
		}
		std::cout << "Check Multiple Components: SUCCESS !" << std::endl;
	}

	if (relaxChecks._checkEdgeManifold) {
		bool is_edge_manifold = igl::is_edge_manifold(V, F);
		if (!is_edge_manifold) {
			throw std::runtime_error("Check Edge manifold - FAILED!");
		}
		std::cout << "Check Edge Manifold: SUCCESS !" << std::endl;
	}

	if (relaxChecks._checkTopology) {
		int euler_char = get_euler_char(V, F);
		if (!euler_char) {
			std::stringstream ss;
			ss << "Input does not have a disk topology, it's euler char is: " << euler_char;
			throw std::runtime_error(ss.str());
		}
		std::cout << "Check Topology: SUCCESS !" << std::endl;
	}

	if (relaxChecks._checkZeroAreaFaces) {
		const double eps = 1e-14;
		for (int i = 0; i < areas.rows(); i++) {
			if (areas(i) < eps) {
				throw std::runtime_error("Check Zero Area Faces - FAILED!");
			}
		}
		std::cout << "Check Zero Area Faces: SUCCESS !" << std::endl;
	}
}

int main(int argc, char *argv[]) {
	int iRes = -1;

	std::vector<std::vector<double> > vV;
	std::vector<std::vector<int> > vF;

	Param_State state;
	StateManager state_manager;
	std::unique_ptr<GlobalLocalParametrization> param_ptr;

	std::vector<float> uv;

	const std::string s_LITERAL_V("v");
	const std::string s_LITERAL_V_SIZE("vs");
	
	const std::string s_LITERAL_F("f");
	const std::string s_LITERAL_F_SIZE("fs");

	const std::string s_LITERAL_Q("q");
	const std::string s_LITERAL_PRE_CALC("p");
	const std::string s_LITERAL_STEP("s");
	const std::string s_LITERAL_UV("u");

	try {
		Zenuvutils::ZenCheckCompliance(argv[0], ZEN_APPNAME);

		while (true) {
			std::string line = "";
			std::getline(std::cin, line);

			try {
				char type[32];
				// Read first word containing type
				if (sscanf(line.c_str(), "%s", type) == 1) {
					if (type == s_LITERAL_Q) {
						break;
					}
					else if (type == s_LITERAL_PRE_CALC) {
						if (vV.size() > 0 && vF.size() > 0) {
							memset(&state, 0, sizeof(Param_State));
							state.method = Param_State::GLOBAL_ARAP_IRLS;
							state.flips_linesearch = true;
							state.update_all_energies = false;
							state.proximal_p = 0.0001;

							if (!igl::list_to_matrix(vV, state.V))
								throw std::runtime_error("Can not convert list to matrix");


							state.v_num = state.V.rows();
							igl::polygon_mesh_to_triangle_mesh(vF, state.F);

							state.f_num = state.F.rows();

							// set uv coords scale
							igl::doublearea(state.V, state.F, state.M); state.M /= 2.;

							state.global_local_energy = Param_State::SYMMETRIC_DIRICHLET;
							state.cnt_flips = false;

							RelaxChecks relaxChecks;

							check_mesh_for_issues(state.V, state.F, state.M, relaxChecks);

							state.mesh_area = state.M.sum();
							state.V /= sqrt(state.mesh_area);
							state.mesh_area = 1;

							param_ptr.reset(new GlobalLocalParametrization(state_manager, &state));
							param_ptr->init_parametrization();

							std::cout << "out.step" << std::endl;
						}
						else
							throw std::runtime_error("Empty data for calc");

						continue;
					}
					else if (type == s_LITERAL_STEP) {
						param_ptr->single_iteration();
						std::cout << "out.step" << std::endl;

						continue;
					}
					else if (type == s_LITERAL_UV) {
						param_ptr->single_iteration();
						
						const auto rowCount = state.uv.rows();
						for (int i = 0; i < rowCount; i++) {
							std::cout << "_u:" << state.uv(i, 0) << " " << state.uv(i, 1) << std::endl;
						}

						break;
					}
					
					// Get pointer to rest of line right after type
					char * l = &line[strlen(type)];

					if (type == s_LITERAL_V_SIZE) {
						unsigned int u_size = 0;
						if (sscanf(l, "%u", &u_size) == 1) {
							vV.resize(u_size);
							std::cout << "out.vlist" << std::endl;
						}
						else
							throw std::runtime_error("Can not parse Vector size");
					}
					else if (type == s_LITERAL_V) {
						unsigned int row;
						double x[3];
						const int scanf_res = sscanf(l, "%u %lf %lf %lf", &row, &x[0], &x[1], &x[2]);
						if (scanf_res == 4) {
							vV[row].resize(3);
							for (int i = 0; i < 3; i++) {
								vV[row][i] = x[i];
							}
							if (row == vV.size() - 1) {
								std::cout << "out.fsize" << std::endl;
							}
							else {
								std::cout << "out.vlist" << std::endl;
							}
						}
						else {
							std::stringstream ss;
							ss << "res=" << scanf_res << " Can not parse Vector list";
							throw std::runtime_error(ss.str());
						}						
					}
					else if(type == s_LITERAL_F_SIZE) {
						unsigned int u_size = 0;
						if (sscanf(l, "%u", &u_size) == 1) {
							vF.resize(u_size);
							std::cout << "out.flist" << std::endl;
						}
						else
							throw std::runtime_error("Can not parse Face size");
					}
					else if (type == s_LITERAL_F) {
						size_t last = 0; size_t next = 0;
						char delimiter = ' ';
						std::string s(l);
						std::vector<int> tempF;
						while ((next = s.find(delimiter, last)) != string::npos) {
							try {
								const int val = std::stoi(s.substr(last, next - last));
								tempF.push_back(val);
							} catch(std::invalid_argument &e) {}
							
							last = next + 1; 
						}
						try {
							const int val = std::stoi(s.substr(last));
							tempF.push_back(val);
						}
						catch (std::invalid_argument &e) {}

						if (tempF.size() <= 1)
							throw std::runtime_error("Faces list empty");

						unsigned int row = tempF[0];
						vF[row] = std::vector<int>(tempF.begin() + 1, tempF.end());

						if (row == vF.size() - 1) {
							std::cout << "out.precalc" << std::endl;
						}
						else {
							std::cout << "out.flist" << std::endl;
						}
					}
					else
						throw std::runtime_error("Command incomplete");
				}
				else
					throw std::runtime_error("Invalid command");
			}
			catch (std::exception &e) {
				std::stringstream ss;
				ss << "Command:[" << line << "] Msg:[" << e.what() << "]";
				throw std::runtime_error(ss.str());
			}
		}

		iRes = 0;
	}
	catch (std::exception &e) {
		std::cout << "ERROR> " << e.what() << std::endl;
	}
	catch (...) {
		std::cout << "ERROR> Unknown error" << std::endl;
	}
	
	std::cout << "quit" << std::endl;

	return iRes;
}

