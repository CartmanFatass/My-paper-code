# Local HMASD navigation overlay

The shell files select environment/map defaults and hyperparameters. Python entry points under
`train/` parse common config, initialize seeds/device and vector environments, choose shared versus
separated runners, then call `runner.run()`. This local file indexes the fixed snapshot; it does
not change training semantics or upstream source.
