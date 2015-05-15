var playing = false;
var audio = document.createElement('audio');
audio.setAttribute("preload", "auto");
audio.autobuffer = true;

var source = document.createElement('source');
source.type = "audio/mpeg";
source.src = "http://139.140.232.18:8000/WBOR";
audio.appendChild(source);

var NP = false;
var refresh = null;

$('#start').click(function () {
	if (!NP) {
		play();
		$('#start').addClass('active');
		$('#stop').removeClass('active');
		$('#record').addClass('play');
		NP = true;
		refresh = null;
		nowPlaying();
	}
});
$('#stop').click(function () {
	if (NP) {
		stop();
		$('#start').removeClass('active');
		$('#stop').addClass('active');
		$('#record').removeClass('play');
		$('#info').html('');
		NP = false;
	}
});

function nowPlaying() {
	$('#info').html('<div class=spinner>B</div>');
	$.getJSON('/updateinfo?ModPagespeed=noscript', function (data) {
		$('#info').html('<p id=song></p><p id=artist></p>');
		$('#song').html(data.song_string);
		$('#artist').html(data.artist_string);
	});
	if (NP && refresh == null) {
		refresh = setTimeout(nowPlaying, 60000);
	}
}

function play() {
	audio.load();
	audio.play();
	playing = true;
}

function stop() {
	audio.pause();
	playing = false;
}