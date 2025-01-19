import unittest

from watch import fastcmd

app = fastcmd.CommandApp()

@app.command('test', 't', description='A test command.')
def test_command(a: int, b: str, c: list[int]):
    return a, b, c

@app.command('sum', description='Sum a list of integers.')
def sum_command(numbers: list[int]):
    return sum(numbers)

@app.command('concat', description='Concatenate strings.')
def concat_command(a: str, b: str):
    return a + b


class CommandAppTest(unittest.TestCase):

    def test_right_arguments(self):
        out = app('test 11 string 1 2 3 4 5 6')
        self.assertEqual(out, (11, 'string', [1, 2, 3, 4, 5, 6]))

    def test_wrong_arguments(self):
        with self.assertRaises(fastcmd.CommandError):
            app('test 11 ')

    def test_sum_command(self):
        out = app('sum 1 2 3 4 5')
        self.assertEqual(out, 15)

    def test_concat_command(self):
        out = app('concat hello world')
        self.assertEqual(out, 'helloworld')

    def test_no_command(self):
        with self.assertRaises(fastcmd.NoCommandError):
            app('')

    def test_unknown_command(self):
        with self.assertRaises(fastcmd.CommandError):
            app('unknown_command 1 2 3')

    def test_command_alias(self):
        out = app('t 11 string 1 2 3 4 5 6')
        self.assertEqual(out, (11, 'string', [1, 2, 3, 4, 5, 6]))

    def test_get_description(self):
        descriptions = app.get_description()
        self.assertTrue(any(desc[0] == 'test' for desc in descriptions))
        self.assertTrue(any(desc[0] == 'sum' for desc in descriptions))
        self.assertTrue(any(desc[0] == 'concat' for desc in descriptions))
        print(app.get_str_description())

    def test_get_str_description(self):
        str_description = app.get_str_description()
        self.assertIn('test or (\'t\',)', str_description)
        self.assertIn('sum', str_description)
        self.assertIn('concat', str_description)


if __name__ == '__main__':
    unittest.main()
