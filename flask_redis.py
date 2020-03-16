from rediscluster import RedisCluster

import warnings
try:
    import redis
except ImportError:
    # We can allow custom provider only usage without redis-py being installed
    redis = None

__all__ = ('Redis', 'FlaskRedis')
__version__ = '0.1.0'


class FlaskRedis(object):
    def __init__(self, app=None, strict=False, config_prefix='REDIS'):
        self._redis_client = None
        self.provider_class = None
        self.config_prefix = config_prefix

        if app is not None:
            self.init_app(app, strict)

    @classmethod
    def from_custom_provider(cls, provider, app=None, **kwargs):
        assert provider is not None

        # We never pass the app parameter here, so we can call init_app
        # ourselves later, after the provider class has been set
        instance = cls(**kwargs)

        instance.provider_class = provider
        if app is not None:
            instance.init_app(app)
        return instance

    def init_app(self, app, strict=False):
        if self.provider_class is None:
            self.provider_class = (
                redis.StrictRedis if strict else redis.Redis
            )

        redis_url = app.config.get(
            '{0}_URL'.format(self.config_prefix), 'redis://localhost:6379/0'
        )
        database = app.config.get('{0}_DATABASE'.format(self.config_prefix))

        if database is not None:
            warnings.warn(
                'Setting the redis database in its own config variable is '
                'deprecated. Please include it in the URL variable instead.',
                DeprecationWarning,
            )

        if isinstance(self.provider_class, redis.Redis) or isinstance(self.provider_class, redis.StrictRedis):
            self._redis_client = self.provider_class.from_url(
                redis_url, db=database, max_connections=128
            )

        else:
            startup_nodes = app.config.get("REDIS_NODES", False)
            if not startup_nodes:
                self._redis_client = redis.Redis.from_url(
                    redis_url, db=database, max_connections=128
                )
            else:
                self._redis_client = self.provider_class(startup_nodes=startup_nodes, max_connections=128)

        # RedisCluster(startup_nodes=startup_nodes=startup_nodes)

        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['redis'] = self

    def __getattr__(self, name):
        return getattr(self._redis_client, name)


class Redis(FlaskRedis):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            'Instantiating Flask-Redis via flask_redis.Redis is deprecated. '
            'Please use flask_redis.FlaskRedis instead.',
            DeprecationWarning,
        )

        super(Redis, self).__init__(*args, **kwargs)
