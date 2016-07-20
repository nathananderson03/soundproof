$(function(){
    var motion_level = 0;
    var activated = false;
    var can_switch = true;
    var lastflip = new Date().getTime();
    var load_count = $('#images').attr('data-load-counts').split(',')
        .map(function(x){return parseInt(x);});
    var load_count_ptr = 0;
    var min_flips = parseInt($('#images').attr('data-min-flips'));

    if(location.hash == '#debug'){
        $('body').addClass('debug');
        $('body').removeClass('animate');
    }
    if(location.hash == '#metadata'){
        $('body').addClass('metadata');
    }
    var last_ts = parseFloat($('#images').attr('data-last-ts'));
    var mod_mode = $('#images').attr('data-moderation');
    var display_id = $('#images').attr('data-display-id');
    var prefetch = function(){
        $.get('/warmup',{
            'display_id':display_id,
            'count':count_required(),
        },function(html){
            $('#images').append(html);
            if(location.hash == '#cam'){
                init_cam();
            }
            else {
                setInterval(activate, 1000);
            }
            setInterval(load,1000*parseInt($('#images').attr('data-speed'), 10));
        });
    };
    var swap_image = function(container, data){
        if(container.hasClass('swappping')){
            return;
        }
        //create a dummy img tag to load and cache the image
        if(!data.src){
            return;
        }
        var dummy = $('<img src="'+data.src+'"/>');
        dummy.hide();
        dummy.one('load',function(){
            //once loaded the image is in cache so we can remove the dummy
            dummy.remove();
            var back = container.find('img').clone();
            back.removeClass('front').addClass('back');
            back.attr('src',data.src);
            back.attr('data-id',data.id);
            back.attr('data-meta',JSON.stringify(data.meta));
            back.attr('data-remote-timestamp',data.remote_timestamp);
            back.attr('data-remote-ts',data.remote_ts);
            back.attr('data-local-timestamp',data.local_timestamp);
            back.attr('data-page-url',data.page_url);
            container.append(back);
            setTimeout(function(){
                container.addClass('flip');
                setTimeout(function(){
                    container.addClass('backstage');
                    container.removeClass('flip');
                    container.find('.front').remove();
                    container.find('.back').removeClass('back').addClass('front');
                    container.removeClass('backstage');
                    container.removeClass('swapping');
                    var swapping = $('.swapping');
                    if(!swapping.length){
                        setTimeout(function(){
                            $('body').removeClass('flipping');
                        },2000);
                    }
                },1000);
            },100);
        });
        $('body').append(dummy);
    };
    var load = function(){
        fixup();
        if($('body').is('.flipping')){
            console.log('load averted - flipping');
            //safety net
            setTimeout(function(){
                $('body').removeClass('flipping');
            },5000);
            return;
        }
        $('body').addClass('flipping');
        var last_ts = parseFloat($('#images').attr('data-last-ts'));
        $('[data-remote-ts]').each(function(){
            var my_ts = parseFloat($(this).attr('data-remote-ts'), 10);
            last_ts = Math.max(last_ts, my_ts);
        });
        var image_ids = [];
        $('.front').each(function(idx, value){ 
            image_ids.push($(value).data('id'));
        });
        $.post('/update',{
            'gt_ts':last_ts,
            'display_id':display_id,
            'image_ids': image_ids.join(","),
            'format':'json',
            'count':load_count[load_count_ptr],
        },function(data){
            if(data.directives){
                process_directives(data.directives);
            }
            if(data.images.length){
                $.each(data.images,function(){
                    //pick a random image to swap
                    var images = $('.img').not('.swapping');
                    var image = $(images[Math.floor(Math.random()*images.length)]);
                    image.addClass('swapping');
                    swap_image(image, this);
                });
            }
            var extra_flips = min_flips - data.images.length;
            for(var n = 0; n < extra_flips; n++){
                var images = $('.img').not('.swapping');
                var image = $(images[Math.floor(Math.random()*images.length)]);
                image.addClass('swapping');
                swap_image(image, get_image_data(image));
            }
            $.each(data.moderated,function(){
                var image = $('img[data-id="'+this.id+'"]').parents('.img');
                if(image.length){
                    image.addClass('swapping');
                    swap_image(image, this.sub);
                }
            });
        }, 'json');
        load_count_ptr += 1;
        load_count_ptr %= load_count.length;
    };
    var get_image_data = function(img){
        var img = img.find('img');
        return {
            'id':img.attr('data-id'),
            'src':img.attr('src'),
            'meta':JSON.parse(img.attr('data-meta')),
            'remote_ts':img.attr('data-remote-ts'),
            'page_url':img.attr('data-page-url'),
        };
    };

    var cooldown = function(t){
        if(!t){
            t = 5000;
        }
        can_switch = false;
        setTimeout(function(){
            can_switch = true;
            if(location.hash != '#cam') {
                deactivate();
            }
        }, t);
    };
    var activate = function(){
        if(activated || !can_switch){
            return;
        }
        activated = true;
        var images = $('img:visible');
        var unseen = images.not('.seen');
        if(unseen.length){
            images = unseen;
        }
        else {
            images.removeClass('seen');
        }
        var img = $(images[Math.floor(Math.random()*images.length)]);
        if(!img.length){
            return;
        }
        img.addClass('seen');
        var blowup = $('.blowup[data-template]').clone();
        blowup.removeAttr('data-template');
        var img_c = img.clone().addClass('clone');
        img_c.removeClass('flip');
        blowup.find('img').replaceWith(img_c);
        if(location.hash == '#metadata'){
            var meta = $.parseJSON(img.attr('data-meta'));
            blowup.find('.username').text(meta.user);
            blowup.find('.likes-count').text(meta.likes);
            blowup.find('.comments-count').text(meta.comments);
            blowup.find('.caption').text(meta.caption);
        }
        if(location.hash == '#debug'){
            blowup.find('.local-timestamp').text(img.attr('data-local-timestamp'));
            blowup.find('.remote-timestamp').text(img.attr('data-remote-timestamp'));
            blowup.find('a').attr('href',img.attr('data-page-url'));
        }
        var padding = 10;
        var full_width_vw = 40;
        var full_width_px = $(window).innerWidth() * full_width_vw / 100 - 2*padding;
        var init_width_px = $('#images .img').width();
        var init_scale = init_width_px/full_width_px;
        var center_left = img.offset().left + img.width()/2;
        var center_top = img.offset().top + img.height()/2;
        var target_left = center_left - full_width_px/2 - padding;
        var target_top = center_top - full_width_px/2 - padding;
        blowup.css({
            'position':'absolute',
            'z-index':1,
            'width':full_width_vw+'vw',
            //'height':'40vw',
            'transform':'scale('+init_scale+')',
            'left':target_left,
            'top':target_top,
        });
        $('#images').append(blowup);
        setTimeout(function(){
            blowup.css({
                'transform':'scale(1)',
                'left':'50%',
                'top':'50%',
                'margin-left':'-20vw',
                'margin-top':'-20vw',
            });
        },50);
        cooldown(7000);
    };
    var deactivate = function(){
        if(!activated || !can_switch){
            return;
        }
        var blowup = $('.blowup').not('[data-template]');
        blowup.css({
            'transform':'scale(0)',
        });
        setTimeout(function(){
            blowup.remove();
        },4000);
        activated = false;
        cooldown(3000);
    };
    var init_cam = function() {
        var canvas = document.getElementById("canvas-blended");

        var ctx = canvas.getContext("2d");
        ctx.fillStyle = "#FF0000";
        ctx.strokeStyle = "#00FF00";
        ctx.lineWidth = 5;

        var camMotion = CamMotion.Engine({
            canvasBlended: canvas
        });
        camMotion.on("frame", function () {
            var point = camMotion.getMovementPoint(true);
            motion_level += camMotion.getAverageMovement(point.x-point.r/2, point.y-point.r/2, point.r, point.r);
            if(motion_level > 40){
                activate();
            }
        });
        camMotion.start();
    };

    var jiggle = function(){
        var images = $('#images .img');
        images.removeClass('jiggle');
        var cols = {};
        images.each(function(){
            var pos = $(this).position();
            var k = pos.left;
            if(k < 0){
                return;
            }
            if(cols[k] === undefined) {
                cols[k] = [];
            }
            cols[k].push($(this));
        });
        var cols_a = [];
        $.each(cols,function(k,v){
            cols_a.push(v);
        });
        var n = 0;
        var f = function(){
            $.each(cols_a[n], function(n, imgs){
                $(imgs).addClass('jiggle');
            });
            n += 1;
            if(n < cols_a.length){
                setTimeout(f,200);
            }
        };
        f();
    };
    var flip_rowcol = function(){
        if(Math.random() > 0.5){
            flip_row();
        }
        else {
            flip_col();
        }
    };
    var flip_row = function(){
        var images = $('#images .img');
        var img_width = images.width();
        var img_height = images.height();
        var row_count = Math.ceil($(window).innerHeight() / img_height);
        var col_count = Math.round($(window).innerWidth() / img_width);
        var row_to_flip = Math.floor(Math.random()*row_count);

        var offset = col_count * row_to_flip;
        var row_images = images.slice(offset, offset+col_count);
        $('body').addClass('flipping');
        $.each(row_images, function(n){
            var img = $(this);
            setTimeout(function(){
                swap_image(img, get_image_data(img));
            }, n*200);
        });
    };
    var flip_col = function(){
        var images = $('#images .img');
        var img_width = images.width();
        var img_height = images.height();
        var row_count = Math.ceil($(window).innerHeight() / img_height);
        var col_count = Math.round($(window).innerWidth() / img_width);
        var col_to_flip = Math.floor(Math.random()*col_count);

        $('body').addClass('flipping');
        for(var n = 0;n < row_count;n++){
            var img = images[n*col_count+col_to_flip];
            if(!img) {
                return;
            }
            setTimeout(function(){
                var img = $(this[0]);
                var n = this[1];
                swap_image(img, get_image_data(img));
            }.bind([img,n]), n*200);
        }
    };
    var count_required = function(){
        var tw = $('#images').attr('data-tilewidth');
        tw = parseFloat(tw.replace('vw',''));
        var h_count = Math.round(100/tw);
        var h_width = $(window).width()/h_count;
        var v_count = Math.ceil($(window).height()/h_width);
        return h_count*v_count;
    };

    var process_directives = function(directives) {
        if(directives.reload){
            location.reload();
        }
        if(directives.location){
            location = directives.location;
        }
    };

    var fixup = function(){
        //detect and fix empty .img divs
        $('.img').each(function(){
            if($(this).children().length == 0) {
                $(this).append($('.img img').clone());
            }
        });
    };

    prefetch();
    if(location.hash == '#cam'){
        setInterval(function(){
            motion_level *= 0.95;
            if(motion_level < 20){
                deactivate();
            }
        }, 50);
    }
    $(document).on('click',flip_rowcol);

    if(location.hash != '#debug'){
        setInterval(function(){
            var t = new Date().getTime();
            if(t > lastflip + 30*1000 && !$('body').is('.flipping')) {
                lastflip = t;
                flip_rowcol();
            }
        }, 1000);
    }
    setInterval(function(){
        location.reload();
    }, 1000*20*60);
});
