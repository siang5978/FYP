$(() => {
    function getSelectedAchievementIds() {
        return $("input[data-achievement-id]:checked")
            .map(function () {
                return $(this).data("achievement-id");
            })
            .get();
    }

    function deleteSelectedAchievements() {
        const ids = getSelectedAchievementIds();
        if (!ids.length) return;

        const target = ids.length === 1 ? "achievement" : "achievements";
        if (!confirm(`Are you sure you want to delete ${ids.length} ${target}?`)) return;

        const requests = ids.map(id => 
            CTFd.fetch(`/api/v1/achievements/${id}`, { method: "DELETE" })
                .then(res => res.json())
        );

        Promise.all(requests)
            .then(results => {
                console.log("Delete results:", results);
                window.location.reload();
            })
            .catch(err => console.error("Delete failed:", err));
    }

    $("#achievements-delete-button").on("click", deleteSelectedAchievements);

    $(document).on("change", "[data-checkbox-all]", function () {
        const checked = $(this).is(":checked");
        $("[data-achievement-id]").prop("checked", checked);
    });

    $(document).on("click", "tr[data-href]", function (e) {
        if ($(e.target).is("input")) return;
        const href = $(this).data("href");
        if (href) window.location.href = href;
    });
});
