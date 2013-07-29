#!/usr/bin/python
import ConfigParser


def main():
    config = ConfigParser.RawConfigParser()
    config.read('.issue')

    for section in config.sections():
        for option in config.options(section):
            print section, option, config.get(section, option)


if __name__ == '__main__':
    main()
