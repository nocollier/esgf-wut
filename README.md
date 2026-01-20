
# esgf-wut

A package in which we try to improve data discovery for the Earth System Grid Federation (ESGF). As a first pass, this package provides a command `wut` and python interface into a database query, mapping facet terms to their collections and projects. We are working on expanding this to include natural language processing to identify likely search parameters from a text prompt.

## Why 'wut'?

Especially for new users, ESGF control vocabulary is hard to understand. We use the internet slang [wut](https://www.urbandictionary.com/define.php?term=wut) to pay homage to the generations of researchers who have frustratedly searched for climate data.

## Usage

### Commandline interface

The package provides a command `wut` which you can use to type control vocabulary (CV) terms and search to what collections/projects they belong. Just call the command and start typing CV terms separated with spaces.

```bash
$ wut gpp canesm5 historical ssp585 mon
                                               TermName
ProjectName CollectionName                             
CMIP3       experiment                       historical
            time_frequency                          mon
CMIP5       experiment                       historical
            time_frequency                          mon
            variable                                gpp
CMIP6       experiment_id          [historical, ssp585]
            frequency                               mon
            source_id                           CanESM5
            variable_id                             gpp
CMIP6Plus   experiment_id                    historical
            frequency                               mon
DRCDP       driving_experiment_id  [historical, ssp585]
            driving_source_id                   CanESM5
input4MIPs  frequency                               mon
obs4MIPs    frequency                               mon
```

By default, `wut` will return results across all supported projects. This can be useful for finding connections between terms and collections across projects. The search is case insensitive, can include wildcards, and will ignore terms that are not in a vocabulary.

```bash
$ wut tAs* not_a_term
                                                                                     TermName
ProjectName CollectionName                                                                   
CMIP3       variable                                                    [tas, tasmin, tasmax]
CMIP5       variable        [tas, tasmax, tasmin, tasAdjust, tasClim, tasmaxClim, tasminClim]
CMIP6       variable_id          [tas, tasmin, tasmax, tasIs, tasLut, tasminCrop, tasmaxCrop]
CMIP6Plus   variable_id                                                 [tas, tasmax, tasmin]
DRCDP       variable_id                                                      [tasmin, tasmax]
input4MIPs  variable_id                                                                   tas
obs4MIPs    variable_id                                                                   tas
```

Note that `wut` only queries a CV database. These projects/collections/terms may not return any dataset results if used to search a supported ESGF index. There are a couple relevant options:

- `--project`: used to return results from only the specified project
- `--format`: used to change the output format (`json` or `yaml`)

```bash
$ wut gpp canesm5 historical ssp585 mon --project cmip6 --format json
{"CMIP6": {"experiment_id": ["historical", "ssp585"], "frequency": "mon", "source_id": "CanESM5", "variable_id": "gpp"}}
```

The idea is that this utility could be used to let users type terms and then use the results to populate actual searches of an ESGF index node.

### Python interface

If you use python as a backend in your ESGF tool, you could use packages functions directly.

```python
from esgf_wut import query_cv_universe,query_df_to_dict

# the query is passed out as a multi-index pandas DataFrame
terms = "tas cesm*"
df = query_cv_universe(terms.split(),project="CMIP6")

# we have a conversion to return a dictionary
query_df_to_dict(df)

>>> {
  "CMIP6": {
    "source_id": [
        "CESM1-1-CAM5-CMIP5",
        "CESM2",
        "CESM1-WACCM-SC",
        "CESM2-WACCM",
        "CESM2-FV2",
        "CESM2-WACCM-FV2",
        "CESM1-CAM5-SE-LR",
        "CESM1-CAM5-SE-HR",
    ],
    "variable_id": "tas",
  }
}
```

