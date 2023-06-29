// 获取所有的父子checkbox
let parents = $(".parent");
let children = $(".child");
// 给每个父checkbox添加点击事件
parents.each(function () {
    $(this).change(function () {
        // 获取当前点击的父checkbox
        let parent_box = $(this);
        // 获取当前点击的父checkbox对应的子checkbox
        let child_boxes = parent_box.closest("tr").find(".child");
        // 获取当前点击的父checkbox对应的custom_box
        let parent_custom_box = parent_box.next(".custom-checkbox");
        // 如果点击前父checkbox是被选中状态，取消选中所有子checkbox
        if (parent_custom_box.hasClass("checked")) {
            // 使父checkbox取消选中，并移除checked样式
            parent_box.prop("checked", false);
            parent_custom_box.removeClass("checked");
            // 子checkbox也取消选中，并移除half-checked样式
            child_boxes.prop("checked", false);
            child_boxes.next(".custom-checkbox").removeClass("half-checked");
        } else { // 如果点击前父checkbox是半选中或未选中状态，选中所有子checkbox
            // 使父checkbox被选中，并添加checked样式，移除half-checked样式
            parent_box.prop("checked", true);
            parent_custom_box.addClass("checked");
            parent_custom_box.removeClass("half-checked");
            // 子checkbox也被选中，并移除checked样式，添加half-checked样式
            child_boxes.prop("checked", true);
            child_boxes.next(".custom-checkbox").removeClass("checked");
            child_boxes.next(".custom-checkbox").addClass("half-checked");
        }
    });
});

// 给每个子checkbox添加点击事件
children.each(function () {
    $(this).change(function () {
        // 获取当前点击的子checkbox
        let child_box = $(this);
        let child_custom_box = child_box.next(".custom-checkbox");
        // 如果点击前子checkbox被选中或半选中
        if (child_custom_box.hasClass("checked") || child_custom_box.hasClass("half-checked")) {
            // 子checkbox取消选中，并移除checked样式和half-checked样式
            child_box.prop("checked", false);
            child_custom_box.removeClass("checked");
            child_custom_box.removeClass("half-checked");
        } else { // 如果点击前子checkbox未选中
            // 子checkbox被选中，并添加checked样式
            child_box.prop("checked", true);
            child_custom_box.addClass("checked");
        }
        // 获取当前点击的子checkbox对应的父checkbox
        let parent_box = child_box.closest("tr").find(".parent");
        let parent_custom_box = parent_box.next(".custom-checkbox");
        // 获取当前点击的子checkbox对应的所有已选中的兄弟checkbox（包括自己）
        let sibling_boxes = child_box.closest("td").find(".child");
        let sibling_custom_boxes = sibling_boxes.next(".custom-checkbox");
        // 统计被选中的兄弟checkbox的数量
        let checkedCount = 0;
        sibling_boxes.each(function () {
            if ($(this).prop("checked"))
                checkedCount++;
        });
        if (checkedCount === sibling_boxes.length) { // 如果所有兄弟checkbox都被选中
            // 则父checkbox也被选中，并添加checked样式，移除half-checked样式
            parent_box.prop("checked", true);
            parent_custom_box.addClass("checked");
            parent_custom_box.removeClass("half-checked");
            // 子checkbox改为半选中
            sibling_custom_boxes.removeClass("checked");
            sibling_custom_boxes.addClass("half-checked");
        } else if (checkedCount === 0) { // 如果没有兄弟checkbox被选中
            // 则父checkbox被取消选中，并移除checked样式或half-checked样式
            parent_box.prop("checked", false);
            parent_custom_box.removeClass("checked");
            parent_custom_box.removeClass("half-checked");
        } else {
            // 否则父checkbox不被选中，但添加half-checked样式，移除checked样式
            parent_box.prop("checked", true);
            parent_custom_box.addClass("half-checked");
            parent_custom_box.removeClass("checked");
            // 其他子checkbox改为全选中
            sibling_boxes.each(function () {
                if ($(this).prop("checked")) {
                    let sibling_custom_box = $(this).next(".custom-checkbox");
                    sibling_custom_box.addClass("checked");
                    sibling_custom_box.removeClass("half-checked");
                }
            });
        }
    });
});

let interval;
update_progress(); // 载入时，当progress==100显示结果
function submit_search() {
    interval = setInterval(update_progress, 100);
    $('.progress-bar').css('width', '0%').attr('aria-valuenow', 0).text(0 + '%');
    // $('#results-form').hide();
    $(".progress").show();
}
//方法一 while循环方式
function sleep(ms) {
    let start = Date.now()
    let end = start + ms
    while(true) {
        if(Date.now() > end) {
            return
        }
    }
}
// 定义一个函数，每隔一秒向/progress发送一个get请求，并根据返回的值更新进度条的宽度和百分比
function update_progress() {
    // $('.progress-bar').css('width', 0 + '%').attr('aria-valuenow', 0).text(0 + '%');
    // $(".progress").show();
    $.get('/progress').done(function (n) {
        $('.progress-bar').css('width', n + '%').attr('aria-valuenow', n).text(n + '%');
        if (n == 100) {
            // 如果进度为100%，就停止轮询，并显示搜索结果
            clearInterval(interval);
            // $('#results-form').show();
            $('#myModal').modal('show');
            // $(".progress").hide();
        }
    }).fail(function () {
        // 如果请求失败，就停止轮询，并显示错误信息
        clearInterval(interval);
        alert('There was an error in getting the progress.');
    });
}
