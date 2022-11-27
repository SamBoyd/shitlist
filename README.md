
![Shitlist](https://github.com/samboyd/shitlist/assets/logo.svg?raw=true)

---

Shitlist is a deprecation tool for python. It checks that deprecated code is only lessened in your codebase by 
testing that any new code doesn't use already deprecated code. 

Add shitlist to your build script to check that deprecated code is gradually remove from your codebase. 

Inspired by a post by Simon Eskildsen, [Shitlist driven development (2016)](https://sirupsen.com/shitlists)

## Installation



```bash
pip install shitlist
```


## Usage

Initialize the config file. This will create a file `.shitlist` in the project root directory
```bash
shitlist init
```

Deprecate some code
```python
import shitlist

@shitlist.deprecate
def old_function():
    pass
```

Update the config file with the newly deprecated code. Shitlist will look for usages of all your deprecated code
and update the config file
```bash
shitlist update
```

Test
```bash
shitlsit test
```
