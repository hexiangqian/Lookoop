// utils.cc
// 常用工具
#include <vector>
#include <string>
#include <map>

#include <fstream>
#include <iostream>
#include <sstream>

#include "utils.h"
#include "FileTool.h"

using namespace std;

/* 生成序列 */
void gen_range(vector<int> &container, int low, int high, int gap, int max_gen) {
    int gen_counter = 0;
    while (low < high && gen_counter < max_gen) {
        if (gap > 0) {
            container.push_back(low);
            low += gap;
        } else {
            container.push_back(high);
            high += gap;
        }
        gen_counter += 1;

    } 
}


/*********************** Data 数据读取 ***********************/
// 检查文件是否存在
void Data::_check() {
    if (!file_exist(_path)) {
        cout << "[WARNING] file does not exit: " << _path << endl;
    }
}


// 读取数据
vector<string> Data::get_data(int col_base) {
    vector<string> container;
    ifstream data_in;
    data_in.open(_path, ios::in);
    if (!data_in.is_open()) {
        cout << "open File Failed." << endl;
        return container;
    }

    string line;
    // 输出类型
    string sigle_data;
    int tmp_col_base;
    while (getline(data_in, line)) {
        istringstream record(line);
        tmp_col_base = col_base;
        while (tmp_col_base > 0) {
            --tmp_col_base;
            record >> sigle_data;
        }
        while (record >> sigle_data) {
            container.push_back(sigle_data);
        }
    }
    return container;
}

void Data::get_data(vector<string> &container, int col_base) {
    container = get_data(col_base);
}
/*********************** end Data ***********************/


/*********************** Trans ***********************/
void Trans::_get_data() {
    if (_p_data.size() == 0) {
        get_data(_p_data);
    }
}


template <typename _tran_type>
_tran_type Trans::convert_to(const std::vector<std::string> &data, const std::string &type) {
    _tran_type new_data;
    for (auto it = data.begin(); it != data.end(); ++it) {
        new_data.push_back(_bin_ops[type](*it));
    }
    return new_data;
}


template <typename _tran_type>
void Trans::convert_to(const std::vector<std::string> &data, _tran_type &new_data, const std::string &type) {
    for (auto it = data.begin(); it != data.end(); ++it) {
        new_data.push_back(_bin_ops[type](*it));
    }
}

// new_data为空容器
template <typename _tran_type>
void Trans::convert_to(_tran_type &new_data, const std::string &type) {
    _get_data();
    for (auto it = _p_data.begin(); it != _p_data.end(); ++it) {
        new_data.push_back(_bin_ops[type](*it));
    }
}

template <typename _tran_type>
_tran_type Trans::convert_to(const std::string &type) {
    _get_data();
    _tran_type new_data, 
    for (auto it = _p_data.begin(); it != _p_data.end(); ++it) {
        new_data.push_back(_bin_ops[type](*it));
    }
    return new_data;
}


// template <typename _t>
// map<string, function<_t(vector<string>)>> Trans::_bin_ops = {
//     {"int", stoi},
//     {"long", string::stol},
//     {"unsigned long", string::stoul},
//     {"float", string::stof},
//     {"double", string::stod}
// };

/*********************** end Trans ***********************/