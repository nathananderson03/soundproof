module.exports = function(grunt) {
    grunt.initConfig({
        less: {
            development: {
                options: {
                    compress: false,
                    yuicompress: true,
                    optimization: 2,
                    paths: ["microsite/static/microsite/less"]
                },
                files: [
                    {
                        "microsite/static/microsite/css/main.css":
                        "microsite/static/microsite/less/main.less"
                    }
                ]
            }
        },
        watch: {
            styles: {
                files: ['microsite/static/microsite/less/**/*.less'], // which files to watch
                tasks: ['less'],
                options: {
                    nospawn: true
                }
            },
        }
    });

    grunt.loadNpmTasks('grunt-contrib-less');
    grunt.loadNpmTasks('grunt-contrib-watch');

    grunt.registerTask('default', ['watch']);
};
