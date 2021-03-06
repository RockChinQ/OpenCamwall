import json
import logging
import time
from pathlib import Path
from mirai import Image

import config
import pkg.chat.manager
import pkg.database.database

import pkg.routines.qzone_routines
import pkg.qzone.model


def new_post_incoming(post_data):
    chat_inst = pkg.chat.manager.get_inst()
    chat_inst.send_message_to_admin_groups([
        "[bot]" +
        "收到新投稿\n" +
        "内容:\n" +
        post_data['text'] + "\n"
                            "图片:" + str(len(json.loads(post_data['media']))) + "张\n" +
        "匿名:" + ("是" if post_data['anonymous'] else "否") + "\n" +
        "QQ:" + str(post_data['qq']) + "\n" +
        "id:##" + str(post_data['id'])
    ])


def post_status_changed(post_id, new_status):
    chat_inst = pkg.chat.manager.get_inst()
    if new_status == '取消':
        chat_inst.send_message_to_admin_groups([
            "[bot]" + "投稿已取消" + "\n" +
            "id:##" + str(post_id)
        ])
    elif new_status == '拒绝':
        db_inst = pkg.database.database.get_inst()
        post = db_inst.pull_one_post(post_id=post_id)
        chat_inst.send_message(target_type='person', target=post['qq'], message="[bot](无需回复)\n您{}的投稿已被拒绝\n"
                                                                                "id:##{}\n内容:{}\n图片:{}张\n原因:{}"
                               .format('匿名' if post['anonymous'] else '不匿名', post_id, post['text'],
                                       str(len(json.loads(post['media']))), post['review']))
    elif new_status == '通过':
        pkg.routines.qzone_routines.clean_pending_posts()


def post_finished(post_id, qq, tid):
    # 验证是否发表成功
    tid_valid = False
    for i in range(4):
        tid_valid = pkg.qzone.model.get_inst().tid_valid(tid)
        if tid_valid:
            break
        time.sleep(3)

    if tid_valid:
        # 发送赞助信息给用户
        if config.sponsor_message != '':
            # 包装消息链
            message_chain=[config.sponsor_message]

            for sponsor_qrcode in config.sponsor_qrcode_path:
                if Path(sponsor_qrcode).exists():
                    message_chain.append(Image(path=sponsor_qrcode))
            pkg.chat.manager.get_inst().send_message("person", qq, message_chain)
            logging.info("发送赞助信息给用户:{}".format(qq))
