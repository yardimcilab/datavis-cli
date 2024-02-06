import click
import os
import yaml
import pandas as pd
import inspect
import seaborn as sns

class UnquotedStr:
    def __init__(self, value):
        self.value = value
    
    def __repr__(self):
        return self.value

def get_method_call_with_defaults(func, prefix, additional_methods=[], exclude_params = [], **kwargs):
    def get_param_defaults(func, override_params={}):
        signature = inspect.signature(func)
        param_defaults = {}
        for name, param in signature.parameters.items():
            # Skip self parameter for methods and **kwargs
            if name == 'self' or param.kind == inspect.Parameter.VAR_KEYWORD:
                continue
            if name in override_params:  # Check if the param is overridden in kwargs
                param_value = repr(override_params[name])
            elif param.default is not param.empty:
                param_value = repr(param.default)
            else:
                param_value = name  # Keep as is for non-default params
            param_defaults[name] = param_value
        return param_defaults

    params_defaults = {}

    # Merge kwargs from additional methods
    for additional_func in additional_methods:
        additional_params_defaults = get_param_defaults(additional_func, kwargs)
        if additional_params_defaults:
            params_defaults.update(additional_params_defaults)
    
    # Main function params and defaults
    main_params_defaults = get_param_defaults(func, kwargs)
    params_defaults.update(main_params_defaults)

    # Exclude params
    for p in exclude_params:
        del params_defaults[p]

    params_str = ',\n'.join([f"{k} = {v}" for k, v in params_defaults.items()])

    full_func_name = f"{prefix}.{func.__name__}" if prefix else func.__name__
    return f"{full_func_name}({params_str})"

def get_import_string(libraries):
    result = []
    for k, v in libraries.items():
        result.append(f"import {k}")
        if v is not None:
            result[-1] += f" as {v}"
    return '\n'.join(result)


@click.group()
def cli():
    """
    CLI tool to output boilerplate code for data loading and visualization
    """
    pass

# Function to create the data loading cell
@click.command()
@click.argument('filename')
@click.argument('dataframe_name')
@click.option('--to_numeric', default=True, help='Convert elements to numeric')
def load_dataframe(filename, dataframe_name, to_numeric):
    cmd = f"""
import pandas as pd
import yaml

with open("{filename}", "r") as file:
    {dataframe_name} = pd.DataFrame(yaml.safe_load(file))"""

    if to_numeric:
        cmd += f"""\n{dataframe_name} = {dataframe_name}.map(lambda e: pd.to_numeric(e, errors='coerce'))\n"""
    cmd += f"""
print({dataframe_name}.head())
print({dataframe_name}.describe())
"""
    click.echo(cmd)

@click.command()
@click.argument('dataframe_name')
def heatmap(dataframe_name):
    """
    Output code to generate Seaborn heatmap
    """

    import_string = get_import_string({"seaborn":"sns", "matplotlib.pyplot":"plt", "colorcet":"cc"})

    comment_string = """
# Default colormap is perceptually-accurate and colorblind-friendly
# See https://colorcet.com/index.html for details
# Displaying the heatmap using seaborn
# For detailed information on the parameters, visit:
# https://seaborn.pydata.org/generated/seaborn.heatmap.html#seaborn.heatmap
    """

    override_defaults = {'data': UnquotedStr(dataframe_name), 'cmap': UnquotedStr('cc.cm.CET_CBL1'), 'method': 'single'}
    method_call_str = get_method_call_with_defaults(sns.heatmap, 'sns', **override_defaults)
    
    result = '\n\n'.join([import_string, comment_string, method_call_str])
    click.echo(result)



@click.command()
@click.argument('dataframe_name')
def clustermap(dataframe_name):
    """
    Output code to generate Seaborn clustermap
    """

    import_string = get_import_string({"seaborn":"sns", "matplotlib.pyplot":"plt", "colorcet":"cc"})

    comment_string = """
# Default colormap is perceptually-accurate and colorblind-friendly
# See https://colorcet.com/index.html for details
# Displaying the clustermap using seaborn
# For detailed information on the parameters, visit:
# https://seaborn.pydata.org/generated/seaborn.clustermap.html#seaborn.clustermap
    """

    override_defaults = {'data': UnquotedStr(dataframe_name), 'cmap': UnquotedStr('cc.cm.CET_CBL1'), 'method': 'single'}
    method_call_str = get_method_call_with_defaults(sns.clustermap, 'sns', additional_methods = [sns.heatmap], exclude_params=['ax', 'cbar_ax'], **override_defaults)
    
    result = '\n\n'.join([import_string, comment_string, method_call_str])
    click.echo(result)

cli.add_command(load_dataframe)
cli.add_command(heatmap)
cli.add_command(clustermap)

if __name__ == '__main__':
    cli()
