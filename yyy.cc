/**************************************************
* This program was generated from Python code
*
**************************************************/

#include <variant>
#include <iostream>
#include <string>

using any = std::variant<int64_t, std::string, void*>;

std::ostream& operator<< (std::ostream& os, any const& v) {
    std::visit([&os](auto const& e){ os << e; }, v);
    return os;
}


void foo(any a, any b)
{
  std::cout << a << " " << b << std::endl;
}

int main()
{
  foo(a, "X");
  return 0;
}

