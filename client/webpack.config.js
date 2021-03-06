const config = {
    entry: [
        './src/AppEntry.js'
    ],
    output: {
        path: __dirname + '/../_15thnight/static',
        filename: 'bundle.js'
    },
	module: {
        loaders: [
            {
                test: /\.js$/,
                exclude: /node_modules/,
                loader: 'babel',
                query: {
                    presets: ['react', 'es2015']
                }
            },
            { test: /\.(png|woff|woff2|eot|ttf|svg)$/, loader: 'url-loader?limit=100000' },
            { test: /\.css$/, loader: "style-loader!css-loader" }
        ]
    },
    resolve: {
        alias: {
            lib: __dirname + '/node_modules',
            actions: __dirname + '/src/actions',
            api: __dirname + '/src/api',
            components: __dirname + '/src/components',
            constants: __dirname + '/src/constants',
            form: __dirname + '/src/components/form',
            pages: __dirname + '/src/components/pages',
            reducers: __dirname + '/src/reducers',
            store: __dirname + '/src/store',
            style: __dirname + '/style',
            table: __dirname + '/src/components/table'
        },
        extensions: ['', '.js', '.jsx', '.css'],
        modulesDirectories: [
          'node_modules'
        ]
    }
};

module.exports = config;
