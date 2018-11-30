//  -------------------------   //
//  Author: Eric Cabral (2018)  //
//           ICMC USP           //
//  -------------------------   //

/*
    Credits to: Petr Devaikin
    https://github.com/petr-devaikin/petr-devaikin.github.io/tree/master/duma
*/


// STRING INTERPOLATION
if (!String.prototype.format) {
  String.prototype.format = function() {
    var args = arguments;
    return this.replace(/{(\d+)}/g, function(match, number) {
      return typeof args[number] != 'undefined'
        ? args[number]
        : match
      ;
    });
  };
}

/*
*   START VIS KT
*/
var userDirectory;

function getUserId () {

	var input = prompt("Please enter your userId","");

	if ((input != null) && (input.trim() != "")) {
		//check if the user exists
		userID = input;
		userDirectory= "../users/{0}/".format(input);
		checkUserExists()
	}
}

getUserId();

// Check if the user exists
function checkUserExists() {
	$.ajax({
		type: "POST",
		url: "./cgi-bin/checkUser.py",
		data: {
            userDirectory:JSON.stringify(userDirectory)
        },
		async: true,
		success: function( msg ) {

            var status = msg['status'];

            if (status == "yes") {
                $("#userWelcome").html("You are logged in as: "+userID);
                userExists = true
                // processUserComands();
            }
            if(status == "no") {
                alert("No such user exists!");
            }
            if (status == "error") {
                alert("Error1 finding the user!");
            }
        },
	    error: function(msg){
		    alert("Error2 finding the user!");
        }
    });
}

//
//   END VIS KT
//

// ZOOM AND DRAGGING
function zoomed() {
  dom.svg.attr("transform", d3.event.transform);
}

var d_sessions, a_sessions,
    a_documents,
    d_fractions, a_fractions,
    d_clusters,
    a_transitions;

$.ajax({
    type: "POST",
    url: "./cgi-bin/sankey.py",
    data: { userDirectory:JSON.stringify(userDirectory)},
    async: true,
    success: function(data) {
        // SESSIONS
        d_sessions = data.sessions;
        a_sessions = Object.keys(d_sessions).map(function(a) {
            return d_sessions[a];
        });

        // DOCUMENTS
        a_documents = data.documents;

        // FRACTIONS
        d_fractions = data.fractions;
        a_fractions = Object.keys(d_fractions).map(function(a) {
            return d_fractions[a];
        });
        a_fractions.reverse();

        // CLUSTERS
        d_clusters = data.clusters;

        // TRANSITIONS
        a_transitions = data.transitions;

        draw();
    }
});

var LEFT_MARGIN = 50,
    TOP_MARGIN = 50,
    SESSION_OFFSET = 150,

    FRACTION_WIDTH = 10,

    SHADOW_K = .1,

    SCALE_Y = 1,

    L_ALL_SES = 'All Documents',
    L_SES = 'Session',
    L_CLUS_SES = 'Sessions {0}',
    L_DPS = '{0} Document{1}'

var dom = {
    svg: undefined,
    sessions: undefined,
    fractions: undefined,
    transitions: undefined,
    defs: undefined,
    documents: undefined,
    header: undefined,
}

var s = {}

//  ------------------  //
//   DOM MANIPULATION   //
//  ------------------  //
function setTitle(name) {
    var counter = dom.documents.selectAll('.doc:not(.hidden)').size();
    // var counter = L_DPS.format(counter);

    dom.header.select('#title').html(name === undefined ? L_ALL_SES : name);

    var str;
    if (counter != 1) {
        str = L_DPS.format(counter, "s");
    } else {
        str = L_DPS.format(counter, "");
    }

    dom.header.select('#supp').text(str);
    //dom.header.select('#counter').text(supp === undefined ? '' : counter);
    dom.header.select('#clear').classed('hidden', name === undefined);
}

function hoverSession(session) {
    s.fractions
        .classed('active', function(d) { return session !== undefined && d.sessionId == session.id; });
    s.fractions
        .classed('active', false);
}

function hoverFraction(fraction) {
    s.fractions
        .classed('active', function(d) { return fraction !== undefined && d.id == fraction.id; });
}

function hoverTransition(transition) {
    s.transitions
        .classed('active', function(d) { return transition !== undefined && d.id == transition.id; });

    s.fractions
        .classed('active', function (d) {
            return transition !== undefined && (d.id == transition.from || d.id == transition.to);
        });
}

function hoverDocument(doc) {
    s.fractions
        .classed('active', function(d) {
            return doc !== undefined && doc.fractionIds.indexOf(d.id) != -1;
        })
        .classed('faded', function(d) {
            if (doc !== undefined)
                return doc.fractionIds.indexOf(d.id) == -1;
            else
                if (noSelection)
                    return false
                else
                    return !d3.select(this).classed('selected');
            });

    s.transitions
        .classed('active', function(d) {
            if (doc === undefined)
                return false;
            var i = doc.fractionIds.indexOf(d.from);
            return i != -1 && doc.fractionIds.indexOf(d.to) == i + 1;
        })
        .classed('faded', function(d) {
            if (doc !== undefined) {
                var i = doc.fractionIds.indexOf(d.from);
                return i == -1 || doc.fractionIds.indexOf(d.to) != i + 1;
            }
            else
                if (noSelection)
                    return false;
                else
                    return !d3.select(this).classed('selected');
        });
}

var noSelection = true;
function clearSelection() {
    if (!noSelection) {
        noSelection = true;

        s.fractions
            .classed('selected', false)
            .classed('faded', false);
        s.transitions
            .classed('selected', false)
            .classed('faded', false);
        s.documents.classed('hidden', false);
    }
}

function selectFraction(fraction) {
    noSelection = false;

    s.fractions
        .classed('selected', function(d) { return d.id == fraction.datum().id; })
        .classed('faded', function(d) { return d.id != fraction.datum().id; });

    s.transitions
        .classed('faded', true)
        .classed('selected', false);


    s.documents
        .classed('hidden', function(d) { return d.fractionIds.indexOf(fraction.datum().id) == -1; });


    setTitle(
        '{0}, {1}&nbsp;{2}'.format(
            fraction.datum()._name,
            d_sessions[fraction.datum().sessionId].number,
            L_SES
        )
    );
}

function selectTransition(transition) {
    noSelection = false;

    s.fractions
        .classed('faded', function(d) { return d.id != transition.datum().from && d.id != transition.datum().to; })
        .classed('selected', function(d) { return d.id == transition.datum().from || d.id == transition.datum().to; });

    s.transitions
        .classed('faded', function(d) { return d.id != transition.datum().id; })
        .classed('selected', function(d) { return d.id == transition.datum().id; });

    s.documents
        .classed('hidden', function(d) {
            var i = d.fractionIds.indexOf(transition.datum().from)
            return i == -1 || d.fractionIds.indexOf(transition.datum().to) != i + 1;
        });


    var title = d_fractions[transition.datum().from].clusterId == d_fractions[transition.datum().to].clusterId ?
        '{0}, {1}&nbsp;→&nbsp;{2}&nbsp;{3}'.format(
            d_fractions[transition.datum().from]._name,
            d_fractions[transition.datum().from]._sessionName,
            d_fractions[transition.datum().to]._sessionName,
            L_SES
        ) :
        '{0},&nbsp;{1} → {2},&nbsp;{3}'.format(
            d_fractions[transition.datum().from]._name,
            d_fractions[transition.datum().from]._sessionName,
            d_fractions[transition.datum().to]._name,
            d_fractions[transition.datum().to]._sessionName
        );

    setTitle(
        title,
        '{0} → {1}'.format(d_fractions[transition.datum().from]._sessionName, d_fractions[transition.datum().to]._sessionName)
    );
}

function selectSession(session) {
    noSelection = false;

    s.fractions
        .classed('selected', function(d) { return d.sessionId == session.datum().id; })
        .classed('faded', function(d) { return d.sessionId != session.datum().id; });

    s.transitions
        .classed('faded', true)
        .classed('selected', false);

    s.documents
        .classed('hidden', function(d) { return d.sessions[session.datum().id - 1].clusterId === undefined; });

    setTitle(
        L_CLUS_SES.format(session.datum().number)
    );
}

function fractionPosition(fraction) {
    return [
        (LEFT_MARGIN + (d_sessions[fraction.sessionId].id - 1) * SESSION_OFFSET),
        SCALE_Y * (fraction.offset + fraction.order * 3) + TOP_MARGIN
    ]
}

function drawSessions() {
    var sessions = dom.sessions.selectAll('.session').data(a_sessions).enter();

    var groups = sessions.append('g')
        .classed('session', true)
        .attr('transform', function(d) { return 'translate({0},{1})'.format(LEFT_MARGIN + (d.id - 1) * SESSION_OFFSET, TOP_MARGIN); });

    var labels = groups.append('g')
        .classed('sessionLabel', true)
        .attr('transform', 'translate(0,-20)')
        .on('mouseover', hoverSession)
        .on('mouseout', function(d) { hoverSession(); })
        .on('click', function(d) {
            event.stopPropagation();
            selectSession(d3.select(this.parentNode));
        });

    labels.append('text')
        .classed('sessionName', true)
        .text(function(d) { return d.name; });

    labels.append('text')
        .classed('sessionNumber', true)
        .attr('y', -15)
        .text(function(d) { return d.number; });
}

function drawTransitions() {
    var transitions = dom.transitions.selectAll('.transition').data(a_transitions).enter();

    var transitionsHover = dom.transitionsHover.selectAll('.transition').data(a_transitions).enter();

    var grads = dom.defs.selectAll('linearGradient')
        .data(a_transitions, function(d) { return d.from + '-' + d.to })
        .enter()
            .append('linearGradient')
            .attr('id', function(d) { return 'g' + d.from + '-' + d.to; })
            .attr('x1', 0)
            .attr('y1', 0)
            .attr('x2', 1)
            .attr('y2', 0);

    grads.append('stop')
        .attr('offset', '0%')
        .attr('stop-color', function(d) { return d_fractions[d.from]._color; });

    grads.append('stop')
        .attr('offset', '100%')
        .attr('stop-color', function(d) { return d_fractions[d.to]._color; });

    function drawHelper(transitions, forHover) {
        var groups = transitions.append('g')
            .classed('transition', true);

        if (forHover !== undefined)
            groups
                .on('mouseover', hoverTransition)
                .on('mouseout', function(d) { hoverTransition(); })
                .on('click', function(d) {
                    event.stopPropagation();
                    selectTransition(d3.select(this));
                });

        var lines1 = groups.filter(function(d) {
            return d_fractions[d.from]._position[1] + d.leftOffset * SCALE_Y == d_fractions[d.to]._position[1] + d.rightOffset * SCALE_Y;
        })

        lines1.append('rect')
            .attr('x', function(d) { return d_fractions[d.from]._position[0] + FRACTION_WIDTH / 2; })
            .attr('y', function(d) { return d_fractions[d.from]._position[1] + d.leftOffset * SCALE_Y; })
            .attr('width', function(d) { return d_fractions[d.to]._position[0] - d_fractions[d.from]._position[0] - FRACTION_WIDTH; })
            .attr('height', function(d) { return d.number * SCALE_Y; })
            .attr('stroke', 'none')
            .attr('fill', function(d) {
                if (forHover === undefined)
                    return 'url(#g{0}-{1})'.format(d.from, d.to);
                else
                    return 'rgba(0, 0, 0, 0)';
            });

        var lines2 = groups.filter(function(d) {
            return d_fractions[d.from]._position[1] + d.leftOffset != d_fractions[d.to]._position[1] + d.rightOffset;
        })

        lines2.append('path')
            .attr('d', function(d) {
                var f1 = d_fractions[d.from],
                    f2 = d_fractions[d.to];
                var result = 'M {0} {1} C {2} {3}, {4} {5}, {6} {7}'.format(
                    f1._position[0] + FRACTION_WIDTH / 2,                       // 0
                    f1._position[1] + (d.leftOffset + d.number / 2) * SCALE_Y,  // 1
                    (f1._position[0] + f2._position[0]) / 2,                    // 2
                    f1._position[1] + (d.leftOffset + d.number / 2) * SCALE_Y,  // 3
                    (f1._position[0] + f2._position[0]) / 2,                    // 4
                    f2._position[1] + (d.rightOffset + d.number / 2) * SCALE_Y, // 5
                    f2._position[0] - FRACTION_WIDTH / 2,                       // 6
                    f2._position[1] + (d.rightOffset + d.number / 2) * SCALE_Y  // 7
                );

                return result;
            })
            .attr('fill', 'none')
            .attr('stroke', function(d) {
                if (forHover === undefined)
                    return 'url(#g{0}-{1})'.format(d.from, d.to);
                else
                    return 'rgba(0, 0, 0, 0)';
            })
            .attr('stroke-width', function(d) {
                if (forHover === undefined || d.number > 5)
                    return d.number * SCALE_Y;
                else
                    return 6;
            });
    }

    drawHelper(transitions);
    drawHelper(transitionsHover, true);

    s.transitions = dom.drawArea.selectAll('.transition');
}

function drawFractions() {
    var fractions = dom.fractions.selectAll('.fraction').data(a_fractions).enter();
    var fractionsHover = dom.fractionsHover.selectAll('.fraction').data(a_fractions).enter();


    var groups = fractions.append('g')
        .classed('fraction', true)
        .attr('transform', function(d) {
            d._position = fractionPosition(d);
            d._color = d_clusters[d.clusterId].color;
            d._name = d_clusters[d.clusterId].name;
            d._sessionName = d_sessions[d.sessionId].number;
            return 'translate({0},{1})'.format(d._position[0], d._position[1]);
        });

    var hoverGroups = fractionsHover.append('g')
        .classed('fraction', true)
        .attr('transform', function(d) {
            return 'translate({0},{1})'.format(d._position[0], d._position[1]);
        })
        .on('mouseover', hoverFraction)
        .on('mouseout', function() { hoverFraction(); })
        .on('click', function() {
            event.stopPropagation();
            selectFraction(d3.select(this));
        });

    groups.append('rect')
        .attr('x', -FRACTION_WIDTH / 2)
        .attr('y', 0)
        .attr('width', FRACTION_WIDTH)
        .attr('height', function(d) { return d.size * SCALE_Y; })
        .attr('fill', function(d) { return d._color; });

    hoverGroups.append('rect')
        .attr('x', -FRACTION_WIDTH / 2)
        .attr('y', function(d) {
            if (d.size < 5)
                return -(5 - d.size) / 2 * SCALE_Y;
            else
                return 0;
        })
        .attr('width', FRACTION_WIDTH)
        .attr('height', function(d) {
            if (d.size < 5)
                return 5 * SCALE_Y;
            else
                return d.size * SCALE_Y;
        })
        .attr('fill', 'rgba(0, 0, 0, 0)');


    var labels = groups.append('g')
        .classed('fractionLabel', true)
        .attr('transform', function(d) {
            var y = 0;
            var x = d.sessionId == 7 ? -13 : 7;
            var toShift = {
                5713: 10,
                5714: 10,
                5707: 10,
                5729: 10,
                5739: 10,
                7000: 20,
                5726: 15,
                5733: 15,
                7004: -12
            }

            if (toShift[d.id] !== undefined) y = toShift[d.id]

            return 'translate({0}, {1})'.format(x, y + 2);
        })
        .attr('text-anchor', function(d) {
            return d.sessionId == 7 ? 'end' : 'start';
        });

    labels.append('rect')
        .attr('y', 0)
        .attr('height', 16);

    labels.append('text')
        .text(function(d) { return d._name; })
        .attr('x', 3)
        .attr('y', 12);

    labels.each(function(d) {
        var bbox = d3.select(this).select('text').node().getBBox();
        d3.select(this).select('rect').attr('x', bbox.x -3 );
        d3.select(this).select('rect').attr('width', bbox.width + 6);
    })

    s.fractions = dom.fractions.selectAll('.fraction');
}

function addDocuments() {
    var documents = dom.documents.selectAll('.docs').data(a_documents).enter().append('div');

    documents
        .classed('doc', true)
        .attr('title', function(d) { return d.name; })
        .on('mouseover', function(d) { hoverDocument(d); })
        .on('mouseout', function(d) { hoverDocument(); })
        .on('click', function(d) { event.stopPropagation(); })
        .append('div')
            .classed('docName', true)
            .text(function(d) {
                return d.name;
            });

    var sessions = documents
        .append('div')
        .classed('depSessions', true)
        .selectAll('depSession').data(function(d) { return d.sessions; }).enter();

    sessions.append('div')
        .classed('depSession', true)
        .classed('empty', function(d) { return d.clusterId === undefined; })
        .style('background-color', function(d) {
            if (d.clusterId !== undefined)
                return d_clusters[d.clusterId].color;
            else
                return 'none';
        })

    s.documents = dom.documents.selectAll('.doc');
}


function scrollEvents() {
    d3.select(document).on('scroll', function() {
        dom.header.classed('scroll', document.body.scrollTop > 0);
    });
}

function draw() {

    if (window.innerHeight < 575 + 85 + 25) {
        SCALE_Y = (575 - TOP_MARGIN - (575 + 85 + 25 - window.innerHeight)) / (575 - TOP_MARGIN);
    }

    if (window.innerWidth < 1000 + 210 + 20) {
        CONVO_OFFSET = (1000 - (1000 + 210 + 20 - window.innerWidth) - 2 * LEFT_MARGIN) / 6;
    }

    dom.svg = d3.select('#sankey svg')
        .call(d3.zoom()
        .scaleExtent([1 / 2, 4])
        .on("zoom", zoomed));
    dom.sessions = dom.svg.select('.sessions');
    dom.fractions = dom.svg.select('.fractions');
    dom.transitions = dom.svg.select('.transitions');
    dom.defs = dom.svg.select('defs');
    dom.documents = d3.select('.docs');
    dom.header = d3.select('#listHeader');
    dom.transitionsHover = d3.select('.hoverTransitions');
    dom.fractionsHover = d3.select('.hoverFractions');
    dom.drawArea = d3.select('svg .drawings');

    drawSessions();
    drawFractions();
    drawTransitions();
    addDocuments();

    setTitle();

    scrollEvents();

    d3.select(window).on('click', function() {
        clearSelection();
        setTitle();
    });
}

