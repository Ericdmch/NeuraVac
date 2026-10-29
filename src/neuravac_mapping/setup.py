from glob import glob
from setuptools import setup
setup(name='neuravac_mapping', version='0.1.0', packages=['neuravac_mapping'],
      data_files=[('share/ament_index/resource_index/packages', ['resource/neuravac_mapping']),
                  ('share/neuravac_mapping', ['package.xml']),
                  ('share/neuravac_mapping/config', glob('config/*.yaml')),
                  ('share/neuravac_mapping/launch', glob('launch/*.py')),
                  ('share/neuravac_mapping/behavior_trees', glob('behavior_trees/*.xml'))],
      install_requires=['setuptools', 'Flask'],
      package_data={'neuravac_mapping': ['templates/*.html']},
      entry_points={'console_scripts': [
          'scan_bridge = neuravac_mapping.scan_bridge:main',
          'dashboard_bridge = neuravac_mapping.dashboard_bridge:main',
          'autonomy_node = neuravac_mapping.autonomy_node:main',
          'autonomy_dashboard = neuravac_mapping.autonomy_dashboard:main']})
