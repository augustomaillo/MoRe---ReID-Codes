import h5py
import numpy as np
from PIL import Image

class Dataset():
    def __init__(self, h5_file, to_bgr):
        """Constructor for MoRe_Dataset class

        Args:
                h5_file: path to hdf5 file with images
                to_bgr: bool to convert data to bgr
        """

        self._h5File = h5_file
        self.to_bgr = to_bgr
        

        self._identNum = dict()
        with h5py.File(h5_file, 'r') as f:
            train_uids = np.unique(list(f['metadata']['train_idsA'].value))
            test_uids = np.unique(list(f['metadata']['test_idsA'].value))

        self._identNum['train'] = train_uids
        self._identNum['test'] = test_uids

        amount = []
        with h5py.File(h5_file, 'r') as f:
            for e in f['metadata'].keys():
                if 'ids' in e:
                    amount.append(len(f['metadata'][e].value))
        self._imgs_amount = sum(amount)


    def content_array(self, partition, cam_name):
        """Returns files names and its ident number

        Args:
                cam_name: a string specifying the camera

        Returns:
                a list with files names
                a numpy array with its ident number
        """  
        cam_name = cam_name[-1]
        with h5py.File(self._h5File, 'r') as f:
            return (list(f['metadata/%s_files%s'%(partition, cam_name)].value), np.asarray(f['metadata/%s_ids%s'%(partition, cam_name)].value, np.int))


    def get_image(self, img_path):
        """Returns image data

        Args:
                img_path: a string specifying image path

        Returns:
                a numpy array containing image data
        """  

        with h5py.File(self._h5File, 'r') as f:
            if self.to_bgr:
                return f['images'][img_path].value[:,:,::-1]
            else:
                return f['images'][img_path].value

    def ident_num(self, partition):
        """Returns the number of uniques ID on dataset
        """  
        return len(self._identNum[partition])

    def images_amount(self):
        """Returns the number of images on dataset
        """
        return self._imgs_amount

class BPReid_Dataset():

    def __init__(self, h5_file, rgb):
        self._infoDict = dict()

        self._h5File = h5_file
        self._IDs = dict()
        self._keys = dict()
        self._rgb = rgb
        print('Using dataset rgb as ', rgb)
                    
        self._IDs['camA'] = []
        self._IDs['camB'] = []

        self._keys['camA'] = []
        self._keys['camB'] = []
        
        with h5py.File(self._h5File, 'r') as f:
            cam = 'camA'

            for img in f[cam].keys():
                if 'camA' in img:
                    self._keys['camA'].append(img)
                    self._IDs['camA'].append(f[cam][img].attrs['ID'])
                elif 'camB' in img:
                    
                    self._keys['camB'].append(img)
                    self._IDs['camB'].append(f[cam][img].attrs['ID'])

        self._identNum = len(
            np.unique(
                np.concatenate(
                    [self._IDs[f] for f in self._IDs.keys()]
                    )
                )
            )

        self._imgs_amount = sum([ len(self._keys[cam]) for cam in self._keys.keys() ])


    def content_array(self, cam_name):
        """Returns files names and its ident number

        Args:
                cam_name: a string specifying the camera

        Returns:
                a list with files names
                a numpy array with its ident number
        """  
        return self._keys[cam_name],np.squeeze(np.array(self._IDs[cam_name]), axis=-1)

    def get_image(self, filename):
        """Returns image data

        Args:
                filename: a string specifying image name

        Returns:
                a numpy array containing image data
        """  

        with h5py.File(self._h5File, 'r') as f:
            # print(type(f[cam][filename]))
            if self._rgb:
                return f['camA'][filename].value[:,:,::-1]
            else:
                return f['camA'][filename].value

    def ident_num(self):
        """Returns the number of uniques ID on dataset
        """  
        return self._identNum

    def images_amount(self):
        """Returns the number of images on dataset
        """
        return self._imgs_amount


class JoiningDatasets():
    def __init__(self, DatasetsList):
        self.camA_images = []
        self.camB_images = []
        self.linknamedt = dict()
        self.linknames = dict()
        self.camA_ids = np.array([])
        self.camB_ids = np.array([])
        self.dt_list = DatasetsList
        
        img_indexA = 1
        img_indexB = 1
        
        max_idA = 0
        max_idB = 0
        
        for idx, dt in enumerate(DatasetsList):
            dtimgA, dtidA = dt.content_array('camA')
            dtimgB, dtidB = dt.content_array('camB')
            for imgname in dtimgA:
                self.linknamedt['imgA_%06d'%img_indexA] = idx
                self.linknames['imgA_%06d'%img_indexA] = imgname
                img_indexA +=1
            for imgname in dtimgB:
                self.linknamedt['imgB_%06d'%img_indexB] = idx
                self.linknames['imgB_%06d'%img_indexB] = imgname
                img_indexB +=1
            
            if(len(dtidA.shape)==2):
                    dtidA = dtidA[:,0]
                    dtidB = dtidB[:,0]
                    
            self.camA_ids = np.append(self.camA_ids, dtidA + max_idA)
            max_idA += dtidA.max()
            
            self.camB_ids = np.append(self.camB_ids, dtidB + max_idB)
            max_idB += dtidB.max()
                    
        for c in self.linknamedt.keys():
            if('imgA' in c):
                self.camA_images.append(c)
            else:
                self.camB_images.append(c)
        
        self._ident_num = len(np.unique(self.camA_ids))
        
    def content_array(self, cam):
        if cam =='camA':
            return self.camA_images,self.camA_ids
        else:
            return self.camB_images,self.camB_ids
        
    def get_image(self, filename):
            dt = self.dt_list[self.linknamedt[filename]]
            return dt.get_image(self.linknames[filename])
    
    def ident_num(self):
        return self._ident_num