import inspect
import os
from typing import Optional


#
# Class to help simplify writing code
#
class Coder:
    code: list = []
    lines: int = 0
    last_indent: int = 0
    rendered_lines: int = 0
    code_type: str = "python"
    comment_string: str = "#"
    indent_space: int = 4
    start_tag: str = "{{ "
    end_tag: str = " }}"

    #
    # init
    #
    def __init__(
        self, code_type="python", indent_space=None, start_tag=None, end_tag=None
    ):
        self.code_type = code_type.lower()
        self.code = []
        self.lines = 0
        self.last_indent = 0
        self.rendered_lines = 0

        if indent_space is not None:
            self.indent_space = indent_space
        else:
            if self.code_type == "python":
                self.indent_space = 4
            elif self.code_type == "dart":
                self.indent_space = 2
            else:
                self.indent_space = 4

        if start_tag is not None:
            self.start_tag = start_tag
        else:
            if self.code_type == "html":
                self.start_tag = "{$ "
            else:
                self.start_tag = "{{ "

        if end_tag is not None:
            self.end_tag = end_tag
        else:
            if self.code_type == "html":
                self.end_tag = " $}"
            else:
                self.end_tag = " }}"

        if self.code_type in ["html", "xml"]:
            self.comment_string = "<!--"
        elif self.code_type in ["yaml", "php", "python"]:
            self.comment_string = "#"
        elif self.code_type == "dart":
            self.comment_string = "//"
        elif self.code_type == "sql":
            self.comment_string = "--"
        else:
            self.comment_string = "#"

    #
    # comment
    #
    def comment(self, indent, comment, same_line=False):
        if indent == -1:
            indent = self.last_indent

        if self.code_type in ["html", "xml"]:
            comment = "<!-- " + comment + " -->"
        elif self.code_type in ["yaml", "php", "python"]:
            comment = "# " + comment
        elif self.code_type == "dart":
            comment = "// " + comment
        elif self.code_type == "sql":
            comment = "-- " + comment
        else:
            comment = "# " + comment

        line = {"indent": indent, "code": comment}
        if not same_line or self.lines == 0:
            self.code.append(line)
            self.lines += 1
            self.last_indent = indent
        else:
            comment_indent = self.indent_space
            if indent > 0:
                comment_indent = self.indent_space * indent
                comment_length = len(self.code[self.lines - 1]["code"])
                if comment_length < comment_indent + 4:
                    comment_indent = comment_indent - comment_length
                else:
                    comment_indent = self.indent_space

            self.code[self.lines - 1]["code"] += " " * comment_indent + comment

    #
    # comment_begin
    #
    def comment_begin(self, indent, comment):
        if indent == -1:
            indent = self.last_indent

        if self.code_type in ["html", "xml"]:
            comment = "<!-- " + comment
        elif self.code_type in ["php", "sql"]:
            comment = "/*\n" + comment
        else:
            comment = "'''\n" + comment

        line = {"indent": indent, "code": comment}
        self.code.append(line)
        self.lines += 1
        self.last_indent = indent

    #
    # comment_end
    #
    def comment_end(self, indent, comment):
        if indent == -1:
            indent = self.last_indent

        if self.code_type in ["html", "xml"]:
            comment = comment + " --!> "
        elif self.code_type in ["php", "sql"]:
            comment = comment + "\n*/"
        else:
            comment = comment + "\n'''"

        line = {"indent": indent, "code": comment}
        self.code.append(line)
        self.lines += 1
        self.last_indent = indent

    #
    # add
    #
    def add(self, indent, code):
        if indent == -1:
            indent = self.last_indent
        line = {"indent": indent, "code": code}
        self.code.append(line)
        self.lines += 1
        self.last_indent = indent

    #
    # add_formatted
    #
    def add_formatted(self, indent, code):
        if indent == -1:
            indent = self.last_indent

        lines = code.splitlines()
        for line in lines:
            self.add(indent, line)

        self.last_indent = indent

    #
    # new_line
    #
    def new_line(self):
        line = {"indent": 0, "code": ""}
        self.code.append(line)
        self.lines += 1

    #
    # block
    #
    def block(self, block_indent, block):
        indent = 0

        if block:
            for block_line in block.code:
                indent = block_line["indent"] + block_indent
                line = {"indent": indent, "code": block_line["code"]}
                self.code.append(line)
                self.lines += 1

        self.last_indent = indent

    #
    # replace_block
    #
    def replace_block(self, tag, block):
        found = None
        i = 0

        # Find tag in code
        for index, line in enumerate(self.code):
            if line["code"].find(self.start_tag + tag + self.end_tag) >= 0:
                found = line
                i = index
                break
            else:
                continue

        # If found, insert block
        if found is not None:
            indent = found["indent"]
            for block_line in block.code:
                block_line_indent = block_line["indent"] + indent
                line = {"indent": block_line_indent, "code": block_line["code"]}
                self.code.insert(i, line)
                i += 1
                self.lines += 1

            self.code.remove(found)
            self.lines = len(self.code)

    #
    # render
    #
    def render(self, context=None):
        if context is not None:
            self.context_replace(context)

        code_string = ""

        if self.code_type == "json":

            # JSON
            code_length = len(self.code)
            for index, line in enumerate(self.code):
                indent_space = line["indent"] * self.indent_space

                try:
                    str_line = str(line["code"])
                except:
                    str_line = "ERROR: " + line["code"].__dict__
                    print(line["code"].__dict__)

                # Make sure json uses " and not '
                str_line = str_line.replace("'", '"')

                # Remove all spaces to compare
                s = str_line.replace(" ", "")
                if s != "" and s[-1:] == "," and index < (code_length - 1):
                    v = s[-2:][0]

                    try:
                        next_line = str(self.code[index + 1]["code"])
                    except:
                        next_line = "ERROR: " + self.code[index + 1]["code"].__dict__
                        print(self.code[index + 1]["code"].__dict__)

                    if v == '"' and next_line[0] != '"':
                        str_line = str_line.rstrip(",")

                    if v == "}" and next_line[0] not in ['"', "{"]:
                        str_line = str_line.rstrip(",")

                code_string += indent_space * " " + str_line + "\n"

        else:

            # Normal
            for line in self.code:
                indent_space = line["indent"] * self.indent_space

                try:
                    str_line = str(line["code"])
                except:
                    str_line = "ERROR: " + line["code"].__dict__
                    print(line["code"].__dict__)

                code_string += indent_space * " " + str_line + "\n"

        # Prepare code and count lines
        text_array = code_string.split("\n")
        self.rendered_lines = len(text_array)

        return code_string

    #
    # search
    #
    def search(self, search):
        result = []

        for line in self.code:
            if line["code"].find(search) >= 0:
                result.append(line)

        return result

    #
    # delete
    #
    def delete(self, search):
        count_val = 0

        for line in self.code:
            if line["code"].find(search) >= 0:
                self.code.remove(line)
                count_val += 1

        self.lines = len(self.code)

        return count_val

    #
    # delete_block
    #
    def delete_block(self, tag):
        end_block = False
        delete = False
        new_code = []

        for line in self.code:
            if line["code"].find(self.start_tag + tag + self.end_tag) >= 0:
                if delete:
                    delete = False
                    end_block = True
                else:
                    delete = True
            if not delete and not end_block:
                new_code.append(line)
            if end_block:
                end_block = False

        self.code = new_code
        self.lines = len(self.code)

    #
    # Import template file into coder
    # Args:
    #   file_path - linux or windows path
    #   file_name - file name with extension
    #   eol - default escape n, but can be overridden
    #   auto_indent - default False, True forces indent according to current coder setup
    #   indent - default 0, only used when auto_indent is True
    #
    def import_template(
        self, file_path, file_name, context=None, eol="\n", auto_indent=False, indent=0
    ):
        _file = os.path.join(file_path, file_name)
        file = open(_file, "r", encoding="utf8")
        data = file.read()
        lines = data.split(eol)
        last_indent_count = 0

        for line in lines:
            nl = line.strip()
            if nl == "":
                self.new_line()
            else:
                indent_count = len(line) - len(line.lstrip())
                if auto_indent:
                    if indent_count > last_indent_count:
                        indent += 1
                    elif indent_count < last_indent_count:
                        indent -= 1

                    last_indent_count = indent_count
                    if indent < 0:
                        indent = 0

                    self.add(indent, nl)

                else:
                    indent_count = int(indent_count / self.indent_space)
                    self.add(indent_count, nl)

        self.lines = len(self.code)

        if context is not None:
            self.context_replace(context)

    #
    # Import template file into coder block, that can be inserted into main code
    # Args:
    #   file_path - linux or windows path
    #   file_name - file name with extension
    #   eol - default escape n, but can be overridden
    #   auto_indent - default False, True forces indent according to current coder setup
    #   indent - start indent, default 0
    #
    def import_template_block(
        self,
        file_path,
        file_name,
        context=None,
        tag=None,
        eol="\n",
        auto_indent=False,
        indent=0,
    ):
        c = Coder()
        c.import_template(file_path, file_name, eol, context, auto_indent, indent)

        if tag is not None:
            self.replace_block(tag, c)

        return c

    #
    # replace_all
    #
    def replace_all(self, tag, replace_with):
        for index, line in enumerate(self.code):
            self.code[index]["code"] = line["code"].replace(
                self.start_tag + tag + self.end_tag, replace_with
            )

    #
    # replace
    #
    def _replace(self, tag, value, path=""):

        if value is None:
            if self.code_type == "python":
                self.replace_all(path + tag, "None")
            elif self.code_type == "html":
                self.replace_all(path + tag, "")
            elif self.code_type == "sql":
                self.replace_all(path + tag, "NULL")
            else:
                self.replace_all(path + tag, "null")

        elif type(value) is bool:
            if self.code_type == "python":
                if value:
                    self.replace_all(path + tag, "True")
                else:
                    self.replace_all(path + tag, "False")

            elif self.code_type == "sql":
                if value:
                    self.replace_all(path + tag, "TRUE")
                else:
                    self.replace_all(path + tag, "FALSE")
            else:
                if value:
                    self.replace_all(path + tag, "true")
                else:
                    self.replace_all(path + tag, "false")

        elif type(value) is str:
            self.replace_all(path + tag, value)

        elif type(value) is int:
            self.replace_all(path + tag, str(value))

        elif type(value) is float:
            self.replace_all(path + tag, str(value))

        elif type(value) is complex:
            self.replace_all(path + tag, str(value))

        elif type(value) is dict:
            for k in value.keys():
                self._replace(k, value[k], path + tag + ".")

        elif type(value) is list:
            pass

        elif type(value) is tuple:
            pass

        elif type(value) is range:
            pass

        elif type(value) is set:
            pass

        elif type(value) is frozenset:
            pass

        elif type(value) is bytes:
            pass

        elif type(value) is bytearray:
            pass

        elif type(value) is memoryview:
            pass

        elif inspect.isclass(type(value)):
            for k, v in value.__dict__.items():
                self._replace(k, v, path + tag + ".")

        else:
            pass

    #
    # context_replace
    #
    def context_replace(self, context):
        if context:
            for k in context.keys():
                self._replace(k, context[k])

    #
    # strip_last
    #
    def strip_last(self, characters: int):
        if self.lines > 0:
            self.code[self.lines - 1]["code"] = self.code[self.lines - 1]["code"][
                0:-characters
            ]

    def remove_last_comma_before_comment(self, line_no: Optional[int] = None):
        if self.lines == 0:
            return
        if line_no is None:
            line_no = self.lines - 1

        # Find #
        line_text = self.code[line_no]["code"]
        if line_text.find(self.comment_string) == -1:
            new_line_text = line_text[0:-1]
            self.code[line_no]["code"] = new_line_text
            return
        line_array = line_text.split(",")
        new_line_text = ""
        for x, l in enumerate(line_array):
            if x == 0:
                new_line_text = l
            else:
                if self.comment_string in l:
                    new_line_text += " " + l
                else:
                    new_line_text += "," + l

        self.code[line_no]["code"] = new_line_text

    #
    # Append last line
    #
    def append(self, line: str):
        if self.lines > 0:
            self.code[self.lines - 1]["code"] = self.code[self.lines - 1]["code"] + line
        else:
            self.a(0, line)

    #
    # clear_all
    #
    def clear_all(self):
        self.code = []
        self.lines = 0
        self.last_indent = 0
        self.rendered_lines = 0

    #
    # render_to_file
    #
    def render_to_file(self, file_path: str, file_name: str, context=None):
        s = self.render(context=context)
        s = s.encode("utf-8")
        _file = os.path.join(file_path, file_name)
        file = open(_file, "wb")
        file.write(s)
        file.close()

    #
    # print
    #
    def print(self):
        s = self.render()
        print(s)

    #
    # help
    #
    @staticmethod
    def help():
        print("Help for coder")
        print("==============")
        print("")
        print("Initialize:")
        print("from coder import Coder")
        print("c = coder('php')")
        print("")
        print("Languages: php, python, dart, html, yaml, xml, sql")
        print("")
        print("Comments")
        print("Normal: c.comment(0, 'comment') where 0 is the indentation")
        print("Start: c.comment_begin(0, 'comment') where 0 is the indetation")
        print("Stop: c.comment_end(0, 'comment') where 0 is the indetation")
        print("")
        print(
            "Code line: c.add(1, 'for x in customers') - indented one, variables can be parsed as well"
        )
        print("c.new_line() - inserts new line")
        print("")
        print("Combining coders")
        print("c1 = Coder('php')")
        print("c2 = Coder('php')")
        print("c2.add(0, 'line 1')")
        print("c2.add(0, 'line 2')")
        print("c1.add(0, 'for x in y')")
        print("c1.block(1, c2) - places c2 lines at current place in c1, indented 1")
        print("")
        print("code = c.render() - renders c to code string")
        print(
            "c.import_template('', 'text.py') - imports text.py into coder from current position"
        )
        print("c.render_to_file('', 'out.py') -  saves c into out.py")
        print("c.print() - prints coder in console")
        print("")
        print(
            "c.replace_all('old string', 'new string') - replace all occurences to another string"
        )
        print(
            "x = c.count('import Sum') - counts lines with the words 'import Sum' in coder"
        )
        print(
            "if c.count('import Sum') = 1 then c.delete('import Sum') - deletes lines with 'import Sum'"
        )
        print("if only one line is present")
        print("")
        print(
            "x = c.rendered_lines - assign lines to x, can only be done after render()"
        )

    # Shorthand for comment
    def c(self, indent, comment, same_line=False):
        self.comment(indent, comment, same_line)

    # Shorthand for comment_begin
    def cs(self, indent, comment):
        self.comment_begin(indent, comment)

    # Shorthand for comment_end
    def ce(self, indent, comment):
        self.comment_end(indent, comment)

    # Shorthand for add
    def a(self, indent, code):
        self.add(indent, code)

    # Shorthand for add_formatted
    def af(self, indent, code):
        self.add_formatted(indent, code)

    # Shorthand for new_line
    def nl(self):
        self.new_line()

    # Shorthand for block
    def b(self, block_indent, block):
        self.block(block_indent, block)

    # Shorthand for replace_block
    def rb(self, tag, block):
        self.replace_block(tag, block)

    # Shorthand for render
    def r(self, context=None):
        return self.render(context=context)

    # Shorthand for search
    def s(self, search):
        return self.search(search)

    # Shorthand for delete
    def d(self, search):
        return self.delete(search)

    # Shorthand for delete_block
    def db(self, tag):
        self.delete_block(tag)

    # Shorthand for import_template
    def it(self, file_path, file_name, eol="\n", auto_indent=False, indent=0):
        self.import_template(
            file_path, file_name, eol, auto_indent=auto_indent, indent=indent
        )

    # Shorthand for import_template_block
    def itb(self, file_path, file_name, eol="\n", auto_indent=False, indent=0):
        return self.import_template_block(
            file_path, file_name, eol, auto_indent=auto_indent, indent=indent
        )

    # Shorthand for replace_all
    def ra(self, tag, replace_with):
        self.replace_all(tag, replace_with)

    # Shorthand for context_replace
    def cr(self, context):
        self.context_replace(context)

    # Shorthand for clear_all
    def ca(self):
        self.clear_all()

    # Shorthand for render_to_file
    def rtf(self, file_path, file_name, context=None):
        self.render_to_file(file_path, file_name, context=context)

    # Shorthand for print
    def p(self):
        self.print()

    # Shorthand for help
    def h(self):
        self.help()


#
# CoderUtilities
#
class CoderUtilities:
    #
    # Imports a python file into coder, that can be inserted into main code
    #
    # Args:
    #   file_path - linux or windows path
    #   file_name - file name with extension
    #   eol - default escape n, but can be overridden
    #   auto_indent - default False, True forces indent according to current coder setup
    #   i - default 0, ident for output code
    #
    # Returns:
    #   Coder object with python code
    #

    @staticmethod
    def python_to_coder(file_path, file_name, eol="\n", auto_indent=False, i=0):
        c = Coder()
        _file = os.path.join(file_path, file_name)
        file = open(_file, "r", encoding="utf8")
        data = file.read()
        lines = data.split(eol)
        indent = 0
        last_indent_count = 0

        for line in lines:
            nl = line.strip()
            if nl == "":
                c.add(i, "c.new_line()")
            else:
                indent_count = len(line) - len(line.lstrip())
                if auto_indent:
                    if indent_count > last_indent_count:
                        indent += 1
                    elif indent_count < last_indent_count:
                        indent -= 1

                    last_indent_count = indent_count
                    if indent < 0:
                        indent = 0

                    if nl.find("# ") == 0:
                        nl = nl.replace("# ", "")
                        c.new_line()
                        c.add(i, "# " + nl)
                        c.add(i, "c.comment(" + str(indent) + ', "' + nl + '")')
                    else:
                        c.add(i, "c.add(" + str(indent) + ', "' + nl + '")')

                else:
                    indent_count = int(indent_count / c.indent_space)
                    if nl.find("# ") == 0:
                        nl = nl.replace("# ", "")
                        c.new_line()
                        c.add(i, "# " + nl)
                        c.add(i, "c.comment(" + str(indent_count) + ', "' + nl + '")')
                    else:
                        c.add(i, "c.add(" + str(indent_count) + ', "' + nl + '")')

        return c

    #
    # Imports a html file into coder, that can be inserted into main code
    #
    # Args:
    #   file_path - linux or windows path
    #   file_name - file name with extension
    #   eol - default escape n, but can be overridden
    #   auto_indent - default False, True forces indent according to current coder setup
    #   i - default 0, ident for output code
    #
    # Returns:
    #   Coder object with python code
    #

    @staticmethod
    def html_to_coder(file_path, file_name, eol="\n", auto_indent=False, i=0):
        c = Coder(code_type="html")
        _file = os.path.join(file_path, file_name)
        file = open(_file, "r", encoding="utf8")
        data = file.read()
        lines = data.split(eol)
        indent = 0
        last_indent_count = 0

        for line in lines:
            nl = line.strip()
            if nl == "":
                c.add(i, "c.new_line()")
            else:
                indent_count = len(line) - len(line.lstrip())
                if auto_indent:
                    if indent_count > last_indent_count:
                        indent += 1
                    elif indent_count < last_indent_count:
                        indent -= 1

                    last_indent_count = indent_count
                    if indent < 0:
                        indent = 0

                    if (nl.find("<!-- ") == 0) or (nl.find(" -->") == 0):
                        nl = nl.replace("<!-- ", "")
                        nl = nl.replace(" -->", "")
                        c.new_line()
                        c.add(i, "# " + nl)
                        c.add(i, "c.comment(" + str(indent) + ', "' + nl + '")')
                    else:
                        c.add(i, "c.add(" + str(indent) + ', "' + nl + '")')

                else:
                    indent_count = int(indent_count / c.indent_space)
                    if (nl.find("<!-- ") == 0) or (nl.find(" -->") == 0):
                        nl = nl.replace("<!-- ", "")
                        nl = nl.replace(" -->", "")
                        c.new_line()
                        c.add(i, "# " + nl)
                        c.add(i, "c.comment(" + str(indent_count) + ', "' + nl + '")')
                    else:
                        c.add(i, "c.add(" + str(indent_count) + ', "' + nl + '")')

        return c

    #
    # Imports a java file into coder, that can be inserted into main code
    #
    # Args:
    #   file_path - linux or windows path
    #   file_name - file name with extension
    #   eol - default escape n, but can be overridden
    #   auto_indent - default False, True forces indent according to current coder setup
    #   i - default 0, ident for output code
    #
    # Returns:
    #   Coder object with python code
    #

    @staticmethod
    def java_to_coder(file_path, file_name, eol="\n", auto_indent=False, i=0):
        c = Coder(code_type="java")
        _file = os.path.join(file_path, file_name)
        file = open(_file, "r", encoding="utf8")
        data = file.read()
        lines = data.split(eol)
        indent = 0
        last_indent_count = 0

        for line in lines:
            nl = line.strip()
            if nl == "":
                c.add(i, "c.new_line()")
            else:
                indent_count = len(line) - len(line.lstrip())
                if auto_indent:
                    if indent_count > last_indent_count:
                        indent += 1
                    elif indent_count < last_indent_count:
                        indent -= 1

                    last_indent_count = indent_count
                    if indent < 0:
                        indent = 0

                    if nl.find("// ") == 0:
                        nl = nl.replace("// ", "")
                        c.new_line()
                        c.add(i, "# " + nl)
                        c.add(i, "c.comment(" + str(indent) + ', "' + nl + '")')
                    else:
                        c.add(i, "c.add(" + str(indent) + ', "' + nl + '")')

                else:
                    indent_count = int(indent_count / c.indent_space)
                    if nl.find("# ") == 0:
                        nl = nl.replace("// ", "")
                        c.new_line()
                        c.add(i, "# " + nl)
                        c.add(i, "c.comment(" + str(indent_count) + ', "' + nl + '")')
                    else:
                        c.add(i, "c.add(" + str(indent_count) + ', "' + nl + '")')

        return c

    #
    # Imports a dart file into coder, that can be inserted into main code
    #
    # Args:
    #   file_path - linux or windows path
    #   file_name - file name with extension
    #   eol - default escape n, but can be overridden
    #   auto_indent - default False, True forces indent according to current coder setup
    #   i - default 0, ident for output code
    #
    # Returns:
    #   Coder object with python code
    #

    @staticmethod
    def dart_to_coder(file_path, file_name, eol="\n", auto_indent=False, i=0):
        c = Coder(code_type="dart")
        _file = os.path.join(file_path, file_name)
        file = open(_file, "r", encoding="utf8")
        data = file.read()
        lines = data.split(eol)
        indent = 0
        last_indent_count = 0

        for line in lines:
            nl = line.strip()
            if nl == "":
                c.add(i, "c.new_line()")
            else:
                indent_count = len(line) - len(line.lstrip())
                if auto_indent:
                    if indent_count > last_indent_count:
                        indent += 1
                    elif indent_count < last_indent_count:
                        indent -= 1

                    last_indent_count = indent_count
                    if indent < 0:
                        indent = 0

                    if nl.find("// ") == 0:
                        nl = nl.replace("// ", "")
                        c.new_line()
                        c.add(i, "# " + nl)
                        c.add(i, "c.comment(" + str(indent) + ', "' + nl + '")')
                    else:
                        c.add(i, "c.add(" + str(indent) + ', "' + nl + '")')

                else:
                    indent_count = int(indent_count / c.indent_space)
                    if nl.find("# ") == 0:
                        nl = nl.replace("// ", "")
                        c.new_line()
                        c.add(i, "# " + nl)
                        c.add(i, "c.comment(" + str(indent_count) + ', "' + nl + '")')
                    else:
                        c.add(i, "c.add(" + str(indent_count) + ', "' + nl + '")')

        return c

    @staticmethod
    def sql_to_coder(file_path, file_name, eol="\n", auto_indent=False, i=0):
        c = Coder(code_type="sql")
        _file = os.path.join(file_path, file_name)
        file = open(_file, "r", encoding="utf8")
        data = file.read()
        lines = data.split(eol)
        indent = 0
        last_indent_count = 0

        for line in lines:
            nl = line.strip()
            if nl == "":
                c.add(i, "c.new_line()")
            else:
                indent_count = len(line) - len(line.lstrip())
                if auto_indent:
                    if indent_count > last_indent_count:
                        indent += 1
                    elif indent_count < last_indent_count:
                        indent -= 1

                    last_indent_count = indent_count
                    if indent < 0:
                        indent = 0

                    if nl.find("-- ") == 0:
                        nl = nl.replace("-- ", "")
                        c.new_line()
                        c.add(i, "-- " + nl)
                        c.add(i, "c.comment(" + str(indent) + ', "' + nl + '")')
                    else:
                        c.add(i, "c.add(" + str(indent) + ', "' + nl + '")')

                else:
                    indent_count = int(indent_count / c.indent_space)
                    if nl.find("-- ") == 0:
                        nl = nl.replace("-- ", "")
                        c.new_line()
                        c.add(i, "-- " + nl)
                        c.add(i, "c.comment(" + str(indent_count) + ', "' + nl + '")')
                    else:
                        c.add(i, "c.add(" + str(indent_count) + ', "' + nl + '")')

        return c

    # Shorthand for python_to_coder
    def ptc(self, file_path, file_name, eol="\n", auto_indent=False, i=0):
        self.python_to_coder(file_path, file_name, eol, auto_indent, i)

    # Shorthand for html_to_coder
    def htc(self, file_path, file_name, eol="\n", auto_indent=False, i=0):
        self.html_to_coder(file_path, file_name, eol, auto_indent, i)

    # Shorthand for java_to_coder
    def jtc(self, file_path, file_name, eol="\n", auto_indent=False, i=0):
        self.java_to_coder(file_path, file_name, eol, auto_indent, i)

    # Shorthand for dart_to_coder
    def dtc(self, file_path, file_name, eol="\n", auto_indent=False, i=0):
        self.dart_to_coder(file_path, file_name, eol, auto_indent, i)
