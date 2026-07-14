# Methodology

## Analytical layers

The explorer keeps three evidence layers separate:

1. **Observed:** country-reported WHO mortality records. These describe reported deaths and are not corrected to a globally comparable model.
2. **Modelled:** GLOBOCAN 2024 incidence, mortality, rates, and cumulative risk. These are internally comparable estimates for one baseline year, not observations in a time series.
3. **Projected:** Cancer Tomorrow demographic scenarios from the 2024 baseline through 2050. These are not observed future outcomes.

## Historical change

Historical mortality change uses WHO country-reported deaths. The primary long-run rate is the crude rate per 100,000 because a complete reproducible age-standardised historical series is not available from the raw WHO files. Crude-rate movement reflects both changes in cancer mortality and changes in population age structure. ICD revision changes can also introduce breaks; the interface exposes source and revision metadata rather than hiding that limitation.

Absolute change, relative change, and compound annual change are calculated only between one record at each endpoint with identical geography, cancer, sex, age, measure, metric, evidence type, and source definition.

## Current cancer mix and age profile

Current rankings use GLOBOCAN 2024 all-age counts for both sexes. Aggregate categories such as “all cancers” are excluded from site rankings. Age peaks use five-year age-specific rates rather than counts, so they are not simply identifying the largest population group.

## Country comparison

Countries are compared only when source edition, evidence type, year, sex, age range, measure, metric, and standard population match. Age-standardised rates using different standards are not treated as interchangeable.

## Projection interpretation

Cancer Tomorrow results are labelled as demographic projections. The base 2024 rate pattern is applied to future population structures unless a scenario explicitly supplies a risk-rate adjustment. A projected increase therefore does not automatically imply that individual cancer risk is rising.

## Uncertainty and rank stability

Where a source supplies lower and upper bounds, a change is labelled uncertain if endpoint intervals overlap. Rankings can use a minimum-volume rule to avoid presenting very small counts as stable league tables. GLOBOCAN does not provide uncertainty intervals in the acquired API response, so its estimates are labelled modelled rather than given false precision claims.

## Prohibited inference

The project does not derive survival from a mortality-to-incidence ratio. It does not combine separate GLOBOCAN releases into a trend, relabel partial registry coverage as national coverage, or describe population-level association as individual causation.
