<%inherit file="layout.mako"/>

<%def name="title()">
    Card colection
</%def>

<%def name="meta_keywords()">

</%def>

<%def name="meta_description()">
    Card collection for fantasy football
</%def>

<link href="/static/footballteams.css?v=1.0" rel="stylesheet">
<div class="row">
    <span class="left">
    <h2>Collection: <a id="leagueLink" target="_blank"></a></h2>
    </span>
</div>
<div id="cardsContainer" class="row">
    <ul class = "tabs blue-grey lighten-4">
    </ul>
    <div id="clubsContainer"></div>
</div>
<script src="/static/collection.js?v=1.0"></script>
