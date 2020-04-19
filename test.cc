#include <functional>
#include <string>
#include <iostream>
#include <sstream>
#include <tuple>
#include <memory>


// Obviously without dynamic types
// e.g. converting only Python code where each variable has specific constant type


using namespace std::string_literals;



//TODO: built-in types with coonversion functions, logic operators etc...

struct String : public std::wstring
{

};


template<typename Base>
struct wrapper 
{
    Base value;

    operator std::string() const
    {
        return std::to_string(value);
    }

    wrapper<Base>& operator+=(const wrapper<Base>& a)
    {
        value += a.value;
        return *this;
    }
};


template<typename Base>
bool operator<(const wrapper<Base>& lhs, const wrapper<Base>& rhs)
{
    return lhs.value < rhs.value;
}

template<typename Base>
bool operator>(const wrapper<Base>& lhs, const wrapper<Base>& rhs)
{
    return lhs.value > rhs.value;
}

struct Bool : public wrapper<bool>
{
};


//TODO: conversion from String


struct Int : public wrapper<long long>
{
};

constexpr Int operator"" _i (unsigned long long n)
{
    return Int{(long long)n};
}

struct Float : wrapper<long double>
{
};

constexpr Float operator"" _f (long double n)
{
    return Float{n};
}

//TODO: optional to string 




//TODO: print function template with variadic args


//TODO; generator == iterator with user-defined next()
// variables are placed into context of lambda, next() calls lambda until it returns None
// TODO: no need for lambda in generators - better to create iterator class and use it with ranges library
// https://stackoverflow.com/questions/9059187/equivalent-c-to-python-generator-pattern
// OR !!!! - Coroutines!


auto make_generator_1()
{
    return [ctx = std::make_unique<std::tuple<Int, std::string>>(0_i, ""s)] () -> std::optional<std::string>
    {
        // generated code
        if (std::get<0>(*ctx) > 3_i) {
            //return None;
            //TODO: How return None anywhere?
            //TODO: None vs std::optional
            //TODO: return value if possible, else optional
            return {};
        }
        //TODO: How to stop generator? Return None and hanlde it in iterator?
        std::get<0>(*ctx) += 1_i;
        std::get<1>(*ctx) += std::get<0>(*ctx);
        return std::get<1>(*ctx);
    };
}





int main()
{
    auto g = make_generator_1();


    for (int i = 0; i < 5; i++) {
        auto s = g();
        std::cout << *s << std::endl;
    }

    auto g1 = make_generator_1();

    for (int i = 0; i < 5; i++) {
        auto s = g1();
        std::cout << *s << std::endl;
    }


    return 0;
}


//TODO: bench 15palindrome converted from python

