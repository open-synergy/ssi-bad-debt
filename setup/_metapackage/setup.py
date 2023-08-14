import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-open-synergy-ssi-bad-debt",
    description="Meta package for open-synergy-ssi-bad-debt Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-ssi_bad_debt_allowance',
        'odoo14-addon-ssi_bad_debt_direct_write_off',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 14.0',
    ]
)
