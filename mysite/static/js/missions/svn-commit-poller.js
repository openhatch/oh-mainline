function poll_svn_commit() {
  $.getJSON("/missions/svn/commit/poll", function(mission_done) {
    if (mission_done) {
      $(".hide_until_svn_commit_mission_is_complete").show();
    } else {
      setTimeout(poll_svn_commit, 5000);
    }
  });
}

setTimeout(poll_svn_commit, 5000);
