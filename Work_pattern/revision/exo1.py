import argparse


def first_option():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input",
                        type=str,
                        default="data/input/function_calling_tests.json",
                        help='input file')
    args = parser.parse_args()
    print(args.input)


def parse_arg():
    parser = argparse.ArgumentParser()
    parser.add_argument('--function_definition',
                        type=str,
                        default='data/input/functions_definition.json',
                        help="function_definition_file, where to get the reference functions.")
    parser.add_argument('--input',
                        type=str,
                        default="data/input/",
                        help="input_file, where to get the input configuration to use.")
    parser.add_argument('--output',
                        type=str,
                        default="data/output/",
                        help="output_file, where to write the output.")
    args = parser.parse_args()
    print(args.function_definition)
    print(args.input)
    print(args.output)


def bad_usage():
    """ j'ai pas besoin d'ecrire des exceptions, il connait l'erreur automatiquement
        il va dans ArgumentError.
        si on met exit_on_error en False, c'est la qu'il crash
    """
    def validate_age(value):
        try:
            age = int(value)
        except ValueError:
            raise argparse.ArgumentTypeError(f"'{value}' is not a valid integer.")
        if not (0 <= age <= 120):
            raise argparse.ArgumentTypeError(f"Age {age} is invalid. Must be 0-120.")
        return age

    parser = argparse.ArgumentParser(exit_on_error=True)
    parser.add_argument("--age", type=validate_age)
    args = parser.parse_args()
    print(args.age)

    # parser = argparse.ArgumentParser(exit_on_error=False)
    # try:
    #     args = parser.parse_args()
    # except argparse.ArgumentError as e:
    #     print(f"Caught error: {e}")   

if __name__ == '__main__':
    # first_option()
    # parse_arg()
    # bad_usage()
