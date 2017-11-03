# -*- coding: utf-8 -*-

import logging
import os
import tempfile

from dbxapi import DbxAPI
from dbxapi import DbxRequest
from dbxobject import FileHandle

remote_dir = '/a'
lip01_tmpfile = tempfile.NamedTemporaryFile(delete=False)
lip10_tmpfile = tempfile.NamedTemporaryFile(delete=False)

lip01_remote = remote_dir + '/lip01.txt'
lip10_remote = remote_dir + '/lip10.txt'

access_token = ''

try:
    scriptpath = os.path.dirname(__file__)
    f = open(scriptpath + '/../ff4d.config', 'r')
    access_token = f.readline()
except Exception as e:
    pass

DbxRequest.access_token = access_token
FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)

initialized = False

def create_env():

    global initialized,remote_dir

    if initialized == True:
        return
    c = DbxAPI()
    c.delete(remote_dir)
    c.create_folder(remote_dir)
    c.create_folder(remote_dir+"/b")
    c.create_folder(remote_dir+"/c")
    c.create_folder(remote_dir+"/d")

    # Local files
    lip01_tmpfile.write(lip01_content)
    lip01_tmpfile.close()

    lip10_tmpfile.write(lip10_content)
    lip10_tmpfile.close()

    # Remote files
    f1 = FileHandle.new_upload_file_handle(lip01_remote)
    f1.buf = lip01_content
    f2 = FileHandle.new_upload_file_handle(lip10_remote)
    f2.buf = lip10_content

    f1 = c.upload(f1)
    c.commit_upload(f1)

    f2 = c.upload(f2)
    c.commit_upload(f2)
    initialized=True


data_invalid_data = {
    'invalid_keyXX': 'A'
}

data_folder_metadata = {
    ".tag": "folder",
    "name": "test",
    "path_lower": "/test",
    "path_display": "/test",
    "id": "id:1REfHwBHqsAAAAAAAAAACA"
}

data_folder_metadata_deleted = {
    ".tag": "deleted",
    "name": "test",
    "path_lower": "/test",
    "path_display": "/test",
    "id": "id:1REfHwBHqsAAAAAAAAAACA"
}

data_error = {
    "error_summary": "path/not_found/.",
    "error": {
        ".tag": "path",
        "path": {
            ".tag": "not_found"
        }
    }
}

data_folder_entries_recursive = {
    ".tag": "folder",
    "name": "test",
    "path_lower": "/test",
    "path_display": "/test",
    "id": "id:1REfHwBHqsAAAAAAAAAACA",
    "entries": [
        {
            ".tag": "folder",
            "name": "test",
            "path_lower": "/test",
            "path_display": "/test",
            "id": "id:1REfHwBHqsAAAAAAAAAACA"
        },
        {
            ".tag": "folder",
            "name": "subfolder",
            "path_lower": "/test/subfolder",
            "path_display": "/test/subfolder",
            "id": "id:1REfHwBHqsAAAAAAAAAACQ"
        },
        {
            ".tag": "folder",
            "name": "ss",
            "path_lower": "/test/ss",
            "path_display": "/test/ss",
            "id": "id:1REfHwBHqsAAAAAAAAAACw"
        },
        {
            ".tag": "folder",
            "name": "aa",
            "path_lower": "/test/aa",
            "path_display": "/test/aa",
            "id": "id:1REfHwBHqsAAAAAAAAAADA"
        },
        {
            ".tag": "folder",
            "name": "aa",
            "path_lower": "/test/subfolder/aa",
            "path_display": "/test/subfolder/aa",
            "id": "id:1REfHwBHqsAAAAAAAAAADQ"
        },
        {
            ".tag": "file",
            "name": "a6w.odt",
            "path_lower": "/test/subfolder/a6w.odt",
            "path_display": "/test/subfolder/a6w.odt",
            "id": "id:1REfHwBHqsAAAAAAAAAACg",
            "client_modified": "2017-09-17T07:17:22Z",
            "server_modified": "2017-09-17T07:17:22Z",
            "rev": "a5c842aa4",
            "size": 19754,
            "content_hash": "1d7c6680d125c441c699120f76f87c84e74a1aead7276fd2c5018497af8e8282"
        },
        {
            ".tag": "file",
            "name": "a",
            "path_lower": "/test/subfolder/a",
            "path_display": "/test/subfolder/a",
            "id": "id:1REfHwBHqsAAAAAAAAAABg",
            "client_modified": "2017-09-15T05:35:34Z",
            "server_modified": "2017-09-17T17:33:06Z",
            "rev": "c5c842aa4",
            "size": 335,
            "content_hash": "c2309f8589e5f21a7c4e1a3b720b4fa8f709f937c704dc674dfe19f6361ac3a0"
        }
    ],
    "cursor": "AAH432X7G062m0KqgB0w6cRsjP2VTQItepKmMFJF-od-NSXIvRJBBegNAPF9wRaJTYfHT_-Um1vVdGrqcqcQm-zNIY9wHbzws59cAt_Pnto0jtKshuuuCUNVxeDkvvatIzqVeu64sIpPIMkt9-Iisc0-62twf_9UBR3SHyUlWAGvmw",
    "has_more": False
}

data_folder_entries = {
    ".tag": "folder",
    "name": "test",
    "path_lower": "/test",
    "path_display": "/test",
    "id": "id:1REfHwBHqsAAAAAAAAAACA",
    "entries": [
        {
            ".tag": "folder",
            "name": "subfolder",
            "path_lower": "/test/subfolder",
            "path_display": "/test/subfolder",
            "id": "id:1REfHwBHqsAAAAAAAAAACQ"
        },
        {
            ".tag": "folder",
            "name": "ss",
            "path_lower": "/test/ss",
            "path_display": "/test/ss",
            "id": "id:1REfHwBHqsAAAAAAAAAACw"
        },
        {
            ".tag": "folder",
            "name": "aa",
            "path_lower": "/test/aa",
            "path_display": "/test/aa",
            "id": "id:1REfHwBHqsAAAAAAAAAADA"
        }
    ],
    "cursor": "AAFBIrM-vZaaJle3YQamJUnntY49rpbUaNvr_G6S2FTNDgOjB_tsvIjKUVzG0ie29yghiCFTqACOY6PGXNPLgtwyAlOXuF8Ho7lppAgfvFDCNbhlfKwfyy-6wQPlZurvfd6RZoceOrd0wdPbNmhxfv6Ww8KgDX9sAbEgvOUsIQ3h7g",
    "has_more": True
}

data_file = {
    ".tag": "file",
    "name": "a6w.odt",
    "path_lower": "/test/subfolder/a6w.odt",
    "path_display": "/test/subfolder/a6w.odt",
    "id": "id:1REfHwBHqsAAAAAAAAAACg",
    "client_modified": "2017-09-17T07:17:22Z",
    "server_modified": "2017-09-17T07:17:22Z",
    "rev": "a5c842aa4",
    "size": 19754,
    "content_hash": "1d7c6680d125c441c699120f76f87c84e74a1aead7276fd2c5018497af8e8282"
}

data_error_path_not_found = {
    "error_summary": "path/not_found/...",
    "error": {
        ".tag": "path",
        "path": {
            ".tag": "not_found"
        }
    }
}

lip01_content = """Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed nisl ipsum, consectetur id hendrerit ut, tristique nec mauris.
Etiam ornare placerat fermentum. Ut dapibus diam fringilla turpis varius feugiat. Donec euismod quis nibh sit amet aliquet.
Donec et scelerisque arcu, a porttitor justo. Donec ultricies congue tellus ut vestibulum. Pellentesque pharetra non ante in vehicula.
Sed convallis massa id ante bibendum, nec iaculis massa rhoncus. Sed volutpat ultricies imperdiet. Nullam sed augue ac felis vestibulum volutpat.
Vivamus vel eros non velit suscipit ullamcorper. Sed at dignissim risus, a tincidunt quam. Donec sit amet ipsum at mauris scelerisque facilisis."""

lip10_content = """Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed nisl ipsum, consectetur id hendrerit ut, tristique nec mauris. Etiam ornare placerat fermentum. Ut dapibus diam fringilla turpis varius feugiat. Donec euismod quis nibh sit amet aliquet. Donec et scelerisque arcu, a porttitor justo. Donec ultricies congue tellus ut vestibulum. Pellentesque pharetra non ante in vehicula. Sed convallis massa id ante bibendum, nec iaculis massa rhoncus. Sed volutpat ultricies imperdiet. Nullam sed augue ac felis vestibulum volutpat. Vivamus vel eros non velit suscipit ullamcorper. Sed at dignissim risus, a tincidunt quam. Donec sit amet ipsum at mauris scelerisque facilisis.
Ut eu tempus magna, sit amet vestibulum sem. Aenean dapibus finibus ipsum, eu sagittis leo lacinia non. Phasellus lobortis, magna quis blandit laoreet, libero mauris sollicitudin nunc, non rhoncus ipsum est ut felis. Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos. Cras vel odio ut ipsum viverra auctor id id risus. Mauris fermentum fermentum felis sed rhoncus. Proin aliquam lobortis fermentum. Suspendisse interdum massa eget orci fermentum gravida. Sed justo tellus, iaculis bibendum mi nec, convallis elementum purus. Mauris bibendum mi ut velit lacinia pellentesque.
Nullam nec tempor ex. Phasellus magna lectus, aliquam ut interdum sit amet, tincidunt et nibh. Duis justo nunc, accumsan non orci id, interdum lobortis libero. Morbi convallis justo et pulvinar laoreet. Vestibulum sapien mauris, dapibus nec facilisis vitae, tempor in massa. Suspendisse tincidunt varius libero sit amet pellentesque. Nullam sagittis magna nec enim sollicitudin, sed tincidunt odio ultricies. Vestibulum laoreet risus eget ipsum facilisis, eget accumsan urna ultrices. Aenean id condimentum odio. Cras feugiat ex vel enim mollis tincidunt.
Morbi lobortis erat in nibh cursus scelerisque. Proin sit amet tortor neque. Morbi rhoncus felis vel tempor faucibus. Fusce libero odio, volutpat ac arcu ut, lobortis pharetra risus. Mauris viverra felis ac ligula pellentesque, sit amet vehicula dui pellentesque. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae; Integer ac orci urna. Quisque sagittis tellus sed varius dapibus. Duis sagittis at ante ut congue. Nullam mattis, sapien non dictum suscipit, velit dui rhoncus mauris, sit amet dictum sapien nisl a libero. Aliquam tincidunt interdum laoreet. Phasellus porttitor elit non mi scelerisque, id maximus velit convallis. In imperdiet mauris velit, sit amet finibus lorem placerat eu. Vivamus vel dolor vitae sapien fringilla luctus nec nec turpis. Nulla facilisi. Sed fermentum rhoncus sapien id condimentum.
Vestibulum et tristique augue, vitae tempor lorem. Vivamus nunc augue, ultricies eu orci vitae, tristique molestie mi. Nullam at pellentesque ligula. Sed luctus nisl a dui consectetur, et cursus turpis lacinia. Etiam diam eros, pretium nec convallis vitae, porta id nisi. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Donec vitae commodo odio. Etiam scelerisque nisi et arcu tempus mattis. Donec auctor, sem ut condimentum facilisis, magna eros elementum nulla, id aliquam est tortor ultricies urna. Nunc a nisl in nibh scelerisque convallis. Fusce tempus, velit a imperdiet facilisis, purus enim viverra sapien, vitae dignissim ex ante euismod arcu. Duis metus erat, faucibus et interdum vel, maximus sit amet justo. Nullam elementum dui sed risus iaculis consectetur. Curabitur tellus enim, varius id est et, luctus vulputate mi. Morbi nisi sapien, dictum ut pellentesque id, blandit et nisi. Suspendisse molestie ac ipsum eget sollicitudin.
Vestibulum rhoncus rhoncus massa, vel fringilla turpis ultricies ac. Nunc vel lobortis arcu. Aliquam erat volutpat. Pellentesque gravida risus id nisi placerat, quis lobortis odio volutpat. Sed sit amet hendrerit quam. Vivamus quis lectus vitae justo eleifend bibendum in quis lorem. Quisque rutrum ullamcorper turpis, ac volutpat augue volutpat in. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae; Suspendisse in nisl diam. Nunc non urna at est ultricies facilisis a faucibus orci. Praesent sit amet sagittis ex. Praesent convallis eu odio eu cursus.
Suspendisse pretium at enim et vestibulum. Ut nunc urna, iaculis a posuere nec, malesuada eget lacus. Donec in sagittis erat, et dictum diam. Cras maximus lobortis ante, eu venenatis tellus dictum eu. Phasellus in ante aliquet, semper eros at, mattis libero. Vivamus sed turpis mauris. Nam justo ante, malesuada rutrum metus ut, ullamcorper viverra lacus. Donec vitae ipsum dapibus, fermentum ipsum mollis, ultrices justo. Maecenas ut urna gravida diam luctus auctor. Nunc sit amet ligula nec urna iaculis aliquam ut sed risus. Fusce efficitur velit quis mauris semper malesuada. Sed a tincidunt purus. Etiam faucibus mauris quis purus sollicitudin, ac varius mi sagittis. Mauris faucibus justo enim, eget tristique metus fringilla dictum. Ut mattis quam sed hendrerit malesuada. Praesent enim quam, tincidunt non faucibus accumsan, vehicula vitae leo.
Nulla at turpis consectetur, mattis erat nec, semper justo. Proin lectus turpis, aliquet a ligula id, lobortis vestibulum velit. Nulla ac felis elementum, lacinia tellus eu, imperdiet risus. Duis faucibus ipsum vel tellus eleifend efficitur. Curabitur quis dui ac risus interdum imperdiet sed nec enim. Donec rhoncus dolor pellentesque neque maximus sagittis. Nullam erat diam, egestas quis vulputate a, semper ac tellus. Sed eleifend ipsum vitae dui rhoncus, aliquet varius nunc egestas. Praesent ultricies, justo fringilla posuere fringilla, nibh massa laoreet ex, eget ornare sem quam eget nulla.
Curabitur quis tortor orci. Proin molestie tellus turpis, in tincidunt odio vestibulum et. Aliquam tempus tincidunt justo quis vestibulum. Sed tempor ligula in dolor efficitur imperdiet. Suspendisse elementum justo non diam pretium placerat. Sed enim felis, rhoncus quis molestie vel, accumsan eget turpis. Aliquam ultrices libero sit amet arcu dictum bibendum. Morbi vitae dapibus mi, sed dignissim lacus. Curabitur cursus vestibulum tellus tincidunt mattis. Fusce sit amet elementum ipsum. Etiam vitae libero velit. Sed iaculis non justo ac sagittis. Ut accumsan libero neque, id elementum massa varius a. Suspendisse potenti. Maecenas finibus nunc neque, sit amet hendrerit sapien lacinia eu.
Vestibulum dignissim nisi neque. In vitae eros eget metus bibendum interdum. Aliquam erat volutpat. Nam faucibus, dui sit amet pulvinar accumsan, mi nisl mollis est, auctor molestie mi sapien quis libero. Cras feugiat tincidunt tortor a tristique. Phasellus dictum sed mauris ut posuere. Quisque gravida magna in molestie sollicitudin. Nunc aliquam ligula id mauris aliquam, quis fringilla neque vehicula. Duis ut faucibus elit, sit amet tristique metus. Orci varius natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Proin nisl nibh, lacinia eget neque quis, porta pretium neque."""


